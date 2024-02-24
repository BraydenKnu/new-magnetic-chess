
#define PIN_EN 2
#define PIN_STEP_A 3
#define PIN_DIR_A 4
#define PIN_STEP_B 5
#define PIN_DIR_B 6
#define PIN_BUTTON 8
#define PIN_12V_SENSE A1

// Incoming command queue
#define QUEUE_SIZE 10
#define COMMAND_LEN 16 // Length of command in chars
int front = 0;
int back = 0;
int count = 0;
unsigned char commandQueue[QUEUE_SIZE][COMMAND_LEN] = {
  "DPX000000Y000000",
  "DPX000000Y000000",
  "DPX000000Y000000",
  "DPX000000Y000000",
  "DPX000000Y000000",
  "DPX000000Y000000",
  "DPX000000Y000000",
  "DPX000000Y000000",
  "DPX000000Y000000",
  "DPX000000Y000000",
};

// Timers
long currentTime = 0;
long motorATimer = 0;
long motorBTimer = 0;
long telemetryTimer = 0;
long executionTimer = 0;

// Timer intervals
int motorAInterval = 10;
int motorBInterval = 10;
int telemetryInterval = 500;
int executionInterval = 50;

// TODO: Measure board size in steps.
const long maxX = 999999;
const long maxY = 999999;

const int optimizeDistanceThreshold; // How close we need to be (euclidian distance) to the target position to start executing the next command.

long motorPosA = 0;
long motorPosB = 0;
bool motorDirA = 0;
bool motorDirB = 0;
long targetPosA = 0;
long targetPosB = 0;
long targetDistanceA = 0;
long targetDistanceB = 0;
long targetDistanceEuclidian = 0;
bool isHomed = false;
bool motorsEnabled = false;
bool magnetUp = false;
bool optimizeRoute = false;

long hypA;
long hypB;
long fastHypotenuse(long a, long b) {
  // Very fast approximation of sqrt(a^2 + b^2) = c
  // See https://stackoverflow.com/questions/3506404/fast-hypotenuse-algorithm-for-embedded-processor

  // Get 0 <= A <= B;
  if (abs(a) > abs(b)) {
    hypA = abs(b);
    hypB = abs(a);
  } else {
    hypA = abs(a);
    hypB = abs(b);
  }
  
  // return hypB + 0.337 * hypA;                // max error ≈ 5.5 %
  // return max(B, 0.918 * (hypB + (hypA>>1))); // max error ≈ 2.6 %
  return hypB + (0.428 * hypA * hypA) / hypB;   // max error ≈ 1.04 %
}

long quick_pow10(long n)
{
    static long pow10[10] = {
        1, 10, 100, 1000, 10000, 
        100000, 1000000, 10000000, 100000000, 1000000000
    };

    return pow10[n]; 
}

void enqueueCommandFromSerial() {
  int newBack = back + 1;
  if (newBack >= QUEUE_SIZE) {
    newBack = 0;
  }
  
  // Check if the queue is full
  if (back == front && count > 0) {
    // Queue is full, ignore and wait for commands to finish, hope serial buffer doesn't overflow before we can read it
    Serial.println("ERROR: Tried to add command to full queue.");
    return;
  }

  // Wait for '#'
  char in = ' ';
  while (in != '#') {
    in = Serial.read();
    if (in != '#') {
      Serial.print("WARNING: Expected '#' preceeding command, got '");
      Serial.write(in);
      Serial.println("'.");
    }
    if (Serial.available() >= COMMAND_LEN) { // Enough chars to contain a full command
      continue;
    } else { // Not enough chars, wait for more.
      return;
    }
  }

  // Read in command
  for (int i = 0; i < COMMAND_LEN; i++) {
    in = Serial.read();
    
    commandQueue[back][i] = in;
  }
  
  Serial.print("Received command: ");
  for (int i = 0; i < COMMAND_LEN; i++) {
    Serial.write(commandQueue[back][i]);
  }
  Serial.println();
  
  count++; // Update count
  back = newBack; // Update the back pointer
}

void dequeueCommand() {
  // Check if the queue is empty
  if (count == 0) {
    return;
  }

  int newFront = front + 1;
  if (newFront >= QUEUE_SIZE) {
    newFront = 0;
  }

  count--; // Update count
  // Dequeue the item at the front index
  // Here, we are just advancing the front pointer
  front = newFront;
}

void sendTelemetry() {
  // Available queue slots
  Serial.print((-motorPosA - motorPosB)/2); // X pos
  Serial.print(",");
  Serial.print((-motorPosA + motorPosB)/2); // Y pos
  Serial.print(",");
  Serial.print(count); // queued command count (not including currently executing)
  Serial.print(",");
  Serial.print(QUEUE_SIZE - count); // Available slots in queue
  Serial.print(",");
  Serial.print(magnetUp ? 'U' : 'D'); // Current status (command format without leading zeros)
  Serial.print(optimizeRoute ? 'O' : 'P');
  Serial.print("X");
  Serial.print((-targetPosA - targetPosB)/2);
  Serial.print("Y");
  Serial.print((-targetPosA + targetPosB)/2);
  Serial.println();
}

long getDigitsFromNextCommand(int startIndex, int numDigits) {
  int endIndex = startIndex + (numDigits - 1);
  if (endIndex >= COMMAND_LEN) {
    Serial.println("ERROR: Tried to get digits after length of the command (index out of range).");
    return 0;
  }

  int index;
  char c;
  int digit;
  long result = 0;
  for (int digitIndex = 0; digitIndex < numDigits; digitIndex++) { // Start at the end (least significant digit) and work our way down.
    index = endIndex - digitIndex;
    c = commandQueue[front][index];
    digit = c - '0'; // Convert char to int
    if (digit >= 0 && digit <= 9) { // Numeric character
      result += quick_pow10(digitIndex) * digit; // Multiply 10's place digit by 10, 100's place digit by 100, etc.
    } else {
      Serial.print("ERROR: Tried to read non-numeric character at command index ");
      Serial.print(index);
      Serial.println(".");
    }
  }

  return result;
}

void executeNextCommand() {
  // Check if there is at least one command in the queue
  if (count <= 0) {
    Serial.println("WARNING: Tried to execute command from empty queue. Ignored.");
    return;
  }
  
  long newTargetX = getDigitsFromNextCommand(3,  6);
  long newTargetY = getDigitsFromNextCommand(10, 6);

  // Check whether this command is valid
  if (!isInPlane(newTargetX, newTargetY)) {
    Serial.print("ERROR: Tried to execute command to move to (");
    Serial.print(newTargetX);
    Serial.print(", ");
    Serial.print(newTargetY);
    Serial.print("), which is outside maximum bounds of rect between (0, 0) and (");
    Serial.print(maxX);
    Serial.print(", ");
    Serial.print(maxY);
    Serial.println("). Command ignored.");
    return;
  }

  // Route settings
  if (commandQueue[front][0] == 'U') { // Magnet up
    magnetUp = true;
  } else if (commandQueue[front][0] == 'D') { // Magnet down
    magnetUp = false;
  }
  optimizeRoute = (commandQueue[front][1] == 'O'); // Optimize route setting (execute next command early to move faster)

  // Target A and B position
  targetPosA = -newTargetX - newTargetY;
  targetPosB = -newTargetX + newTargetY;
  
  dequeueCommand(); // Remove the command from the queue.
}

bool isInPlane(long x, long y) {
  return (x >= 0) && (x <= maxX) && (y >= 0) && (y <= maxY);
}

void step(bool motorA, bool motorB, bool dirA, bool dirB) {
  // Ensure directions are correct
  if (motorA && (dirA != motorDirA)) {
    motorDirA = dirA;
    digitalWrite(PIN_DIR_A, (dirA ? HIGH : LOW));
  }
  if (motorB && (dirB != motorDirB)) {
    motorDirB = dirB;
    digitalWrite(PIN_DIR_B, (dirB ? HIGH : LOW));
  }
  
  if (motorA) {
    digitalWrite(PIN_STEP_A, HIGH);
    motorPosA += (dirA ? 1 : -1);
  }
  if (motorB) {
    digitalWrite(PIN_STEP_B, HIGH);
    motorPosB += (dirB ? 1 : -1);
  }
  
  delay(1); // Arbitrarily chosen step pulse length, increase if controllers ignore it.
  
  digitalWrite(PIN_STEP_A, LOW);
  digitalWrite(PIN_STEP_B, LOW);
}

bool home() {
  // TODO: Implement homing function
  motorPosA = 0;
  motorPosB = 0;
  targetPosA = 0;
  targetPosB = 0;
  
  return true;
}

void setup() {
  
  // put your setup code here, to run once:
  Serial.begin(9600);
  
  pinMode(PIN_STEP_A, OUTPUT);
  pinMode(PIN_DIR_A, OUTPUT);
  pinMode(PIN_STEP_B, OUTPUT);
  pinMode(PIN_DIR_B, OUTPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pinMode(PIN_12V_SENSE, INPUT);
  pinMode(PIN_EN, OUTPUT);

  digitalWrite(PIN_EN, HIGH); // Ensure motors are off
  motorsEnabled = false;
  
  home();

  currentTime = millis();
  motorATimer = currentTime;
  motorBTimer = currentTime;
  telemetryTimer = currentTime;
  executionTimer = currentTime;
}

bool readyToExecute;
void loop() {
  currentTime = millis();

  if (currentTime >= motorATimer) {
    targetDistanceA = targetPosA - motorPosA;
    
    if (targetDistanceA < 0) {
      step(true, false, false, false);
      targetDistanceA++;
    } else if (targetDistanceA > 0) {
      step(true, false, true, false);
      targetDistanceA--;
    }

    motorATimer += motorAInterval;
  }

  else if (currentTime >= motorBTimer) {
    targetDistanceB = targetPosB - motorPosB;
    
    if (targetDistanceB < 0) {
      step(false, true, false, false);
      targetDistanceB++;
    } else if (targetDistanceB > 0) {
      step(false, true, false, true);
      targetDistanceB--;
    }

    motorBTimer += motorBInterval;
  }

  else if (currentTime >= executionTimer) {
    if (count > 0) {
      if (!motorsEnabled) {
        digitalWrite(PIN_EN, LOW); // Enable motors
        motorsEnabled = true;
      }
      
      // Make decision whether to start executing command.
      if (optimizeRoute) { // Start next command when we're almost finished with our current one. Useful for changing commands quickly when carrying pieces.
        targetDistanceEuclidian = fastHypotenuse(targetDistanceA, targetDistanceB);
        readyToExecute = (targetDistanceEuclidian <= optimizeDistanceThreshold);
      } else { // Precise routing: Ensure we are in exactly correct position before starting the next command. Useful for placing pieces correctly.
        readyToExecute = (targetDistanceA == 0 && targetDistanceB == 0);
      }
  
      if (readyToExecute) {
        executeNextCommand();
      }
    } else {
      if (motorsEnabled && targetDistanceA == 0 && targetDistanceB == 0) {
        digitalWrite(PIN_EN, HIGH);
        motorsEnabled = false;
      }
    }
    
    executionTimer += executionInterval;
  }

  else if (currentTime >= telemetryTimer) {
    sendTelemetry();

    telemetryTimer += telemetryInterval;
  }

  // Read any new serial messages (commands)
  else if (Serial.available() >= COMMAND_LEN + 1) { // New command in serial buffer
    enqueueCommandFromSerial();
  }
}

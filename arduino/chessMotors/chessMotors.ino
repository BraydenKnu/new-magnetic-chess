
// Stepper drivers
#define PIN_EN_A 2
#define PIN_DIR_A 3
#define PIN_STEP_A 4
#define PIN_EN_B 5
#define PIN_DIR_B 6
#define PIN_STEP_B 7

// Multiplexed reed switches
#define PIN_MUX_SIG 8
#define PIN_MUX_RANK_S0 A1
#define PIN_MUX_RANK_S1 A2
#define PIN_MUX_RANK_S2 A3
#define PIN_MUX_FILE_S0 A4
#define PIN_MUX_FILE_S1 A5
#define PIN_MUX_FILE_S2 A6
#define PIN_MUX_FILE_S3 A7
#define PIN_ARCADE_BUTTON_SIG 12

// Limit switches
#define PIN_LIM_X 9
#define PIN_LIM_Y 10

// Electromagnet
#define PIN_MAGNET 11

#define SERIAL_BAUD_RATE 115200

// Incoming command queue
#define QUEUE_SIZE 2
#define COMMAND_LEN 12 // Length of command in chars

#define OVERSHOOT_CALIBRATION 30 // Euclidian distance in XY coordinates to overshoot piece movement (magnet up commands)
const int 

int front = 0;
int back = 0;
int count = 0;
unsigned char commandQueue[QUEUE_SIZE][COMMAND_LEN] = {
  "DPX0000Y0000",
  "DPX0000Y0000",
};

// Timers
long currentTime = 0;
long currentTimeMicros = 0;
long motorTimer = 0;
long telemetryTimer = 0;
long executionTimer = 0;

// Timer intervals
int motorIntervalMicros = 800;
int telemetryInterval = 5;
int executionInterval = 50;

// Boundaries (implied bounds at minX=0, minY=0)
const long maxX = 1860;
const long maxY = 2630;

const int optimizeDistanceThreshold = 0; // How close we need to be (euclidian distance) to the target position to start executing the next command.

// Initial values
long motorPosA = 0;
long motorPosB = 0;
long targetPosA = 0;
long targetPosB = 0;
long targetDistanceA = 0;
long targetDistanceB = 0;
long targetDistanceEuclidian = 0;
bool motorDirA = true;
bool motorDirB = true;
bool motorsEnabled = false;
bool magnetUp = false;
bool optimizeRoute = false;
bool tempAStep = false;
bool tempBStep = false;
bool readyToExecute = false;
bool hasIdlePosition = false;
long idleA;
long idleB;
int currentTelemetryChunk = 0;

/*  REED SWITCH INDEXING - Indexed by reedSwitchValues[column][row]
 *      _________ _________________
 *    7 |_|_|_|_| |_|_|_|_|_|_|_|_|
 *    6 |_|_|_|_| |_|_|_|_|_|_|_|_|
 *    5 |_|_|_|_| |_|_|_|_|_|_|_|_|
 *    4 |_|_|_|_| |_|_|_|_|_|_|_|_|
 *    3 |_|_|_|_| |_|_|_|_|_|_|_|_|
 *    2 |_|_|_|_| |_|_|_|_|_|_|_|_|
 *    1 |_|_|_|_| |_|_|_|_|_|_|_|_|
 *    0 |_|_|_|X| |_|_|_|_|_|_|_|_|
 *       0 1 2 3   4 5 6 7 8 9 1011
 *             ^
 *    Example: Square X's value is stored in reedSwitchValues[3][0]
 */
bool reedSwitchValues[12][8];
bool inputButtonValues[] = {false, false, false, false, false, false};

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

const char hexDigits[16] = "0123456789abcdef";
char binToHexCharacter(bool binDigit3, bool binDigit2, bool bool binDigit1, bool binDigit0) {
  return hexDigits[(binDigit3 << 3) + (binDigit2 << 2) + (binDigit1 << 1) + (binDigit0)];
}

void printReedSwitchValuesFromColumn(int column) {
  Serial.print(binToHexCharacter( // bits 4-7 of column in hex
    reedSwitchValues[column][7],
    reedSwitchValues[column][6],
    reedSwitchValues[column][5],
    reedSwitchValues[column][4]
  ));
  Serial.print(binToHexCharacter(
    reedSwitchValues[column][3],
    reedSwitchValues[column][2],
    reedSwitchValues[column][1],
    reedSwitchValues[column][0]
  ));
}

static long pow10[10] = {
  1,
  10,
  100,
  1000,
  10000,
  100000,
  1000000,
  10000000,
  100000000,
  1000000000
};
long quick_pow10(long n)
{
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

void updateSwitchesAndButtons() {
  // TODO: Implement this function. Assigned to Brayden.

  // You might try this algorithm:
  //
  // for each column:
  //   set the PIN_MUX_FILE_S0 through PIN_MUX_FILE_S3 input pins correctly to select the correct column.
  //   // Probably fastest to write bit 0 of column counter to PIN_MUX_FILE_S0, bit 1 to PIN_MUX_FILE_S1.
  //   for each row:
  //     set the PIN_MUX_RANK_S0 through PIN_MUX_RANK_S2 input pins correctly to select the correct row.
  //     set reedSwitchValues[column][row] to the value you read from PIN_MUX_SIG.
  //     if row < 6, set inputButtonValues[row] to the value you read from PIN_ARCADE_BUTTON_SIG, since it shares multiplexer select pins with the row mux.
  //     // Note that (digitalRead(PIN_MUX_SIG) == LOW) evaluates as true if the reed switch is activated, false otherwise.
  //
  // 
}

void sendTelemetry() {
  // Sends portions of the telemetry data.
  // We split it into chunks to avoid sending too much at once, which holds up the rest of our system.
  if (currentTelemetryChunk >= 9) { // Wrap around to beginning of message.
    currentTelemetryChunk = 0;
  }
  switch (currentTelemetryChunk) {
    case 0:
      Serial.print(count); // queued command count (not including currently executing)
      break;
    case 1:
      Serial.print(',');
      Serial.print(QUEUE_SIZE - count); // Available slots in queue
      Serial.println(); // End of message
      break;
    case 2:
      // Start sending reed switch values in big-endian format (most significant bytes first)
      Serial.print(',');
      printReedSwitchValuesFromColumn(11); 
      printReedSwitchValuesFromColumn(10); 
      break;
    case 3:
      printReedSwitchValuesFromColumn(9);
      printReedSwitchValuesFromColumn(8);
      break;
    case 4:
      printReedSwitchValuesFromColumn(7);
      printReedSwitchValuesFromColumn(6);
      break;
    case 5:
      printReedSwitchValuesFromColumn(5);
      printReedSwitchValuesFromColumn(4);
      break;
    case 6:
      printReedSwitchValuesFromColumn(3);
      printReedSwitchValuesFromColumn(2);
      break;
    case 7:
      printReedSwitchValuesFromColumn(1);
      printReedSwitchValuesFromColumn(0);
      break;
    case 8:
      // Arcade-style buttons
      Serial.print(',');
      Serial.print(binToHexCharacter(
        false,
        false,
        inputButtonValues[5],
        inputButtonValues[4]
      ));
      Serial.print(binToHexCharacter(
        inputButtonValues[3],
        inputButtonValues[2],
        inputButtonValues[1],
        inputButtonValues[0]
      ));
      Serial.println(); // End of message
      break;
    default:
      print("ERROR: Ran out of telemetry chunks without resetting");
      currentTelemetryChunk = 0;
  }
  currentTelemetryChunk++;
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
  
  long newTargetX = getDigitsFromNextCommand(3, 4);
  long newTargetY = getDigitsFromNextCommand(8, 4);

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
    dequeueCommand(); // Remove the illegal command from the queue.
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

void step(bool motorA, bool motorB, bool dirA, bool dirB, bool updateTargets) {
  // Ensure directions are correct
  if (motorA && (dirA != motorDirA)) {
    motorDirA = dirA;
    digitalWrite(PIN_DIR_A, (dirA ? LOW : HIGH));
  }
  if (motorB && (dirB != motorDirB)) {
    motorDirB = dirB;
    digitalWrite(PIN_DIR_B, (dirB ? LOW : HIGH));
  }
  
  if (motorA) {
    digitalWrite(PIN_STEP_A, HIGH);
    motorPosA += (dirA ? 1 : -1);
    if (updateTargets) {
      targetDistanceA -= (dirA ? 1 : -1);
    }
  }
  if (motorB) {
    digitalWrite(PIN_STEP_B, HIGH);
    motorPosB += (dirB ? 1 : -1);
    if (updateTargets) {
      targetDistanceB -= (dirA ? 1 : -1);
    }
  }
  
  delayMicroseconds(400);
  
  digitalWrite(PIN_STEP_A, LOW);
  digitalWrite(PIN_STEP_B, LOW);
}

void abortMission() {
  // Disable motors
  digitalWrite(PIN_EN_A, HIGH);
  digitalWrite(PIN_EN_B, HIGH);

  // Disable magnet
  digitalWrite(PIN_MAGNET, LOW);

  // Notify user
  Serial.println("Disabled motors, magnet, and suspended all Arduino processes.");
  
  while (true) {} // Get stuck in an infinite loop intentionally
}

long tempCount;
void home() {
  // Move in -x direction until we hit the switch or go for maxX steps
  tempCount = 0;
  while (tempCount < maxX) {
    if (digitalRead(PIN_LIM_X) == LOW) { // Hit the limit switch
      break;
    }
    else {
      step(true, true, true, true, false); // Step in -x direction
      delayMicroseconds(motorIntervalMicros);
    }
    tempCount++;
  }

  // Error handling
  if (tempCount >= maxX) { // Uh oh, we moved the full width of the board and didn't hit the X limit switch
    Serial.print("ERROR Fatal: Home sequence did not contact X-axis limit switch.");
    abortMission();
  }

  // Move in -y direction until we hit the switch or go for maxY steps
  tempCount = 0;
  while (tempCount < maxY) {
    if (digitalRead(PIN_LIM_Y) == LOW) { // Hit the limit switch
      break;
    }
    else {
      step(true, true, true, false, false); // Step in -y direction
      delayMicroseconds(motorIntervalMicros);
    }
    tempCount++;
  }

  // Error handling
  if (tempCount >= maxY) { // Uh oh, we moved the full width of the board and didn't hit the X limit switch
    Serial.print("ERROR Fatal: Home sequence did not contact Y-axis limit switch.");
    abortMission();
  }

  // Reset values
  motorPosA = 0;
  motorPosB = 0;
  targetPosA = 0;
  targetPosB = 0;
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(SERIAL_BAUD_RATE);

  pinMode(PIN_EN_A, OUTPUT);
  pinMode(PIN_DIR_A, OUTPUT);
  pinMode(PIN_STEP_A, OUTPUT);
  pinMode(PIN_EN_B, OUTPUT);
  pinMode(PIN_DIR_B, OUTPUT);
  pinMode(PIN_STEP_B, OUTPUT);
  
  pinMode(PIN_MUX_SIG, INPUT_PULLUP);
  pinMode(PIN_ARCADE_BUTTON_SIG, INPUT_PULLUP);

  pinMode(PIN_MUX_RANK_S0, OUTPUT);
  pinMode(PIN_MUX_RANK_S1, OUTPUT);
  pinMode(PIN_MUX_RANK_S2, OUTPUT);
  pinMode(PIN_MUX_FILE_S0, OUTPUT);
  pinMode(PIN_MUX_FILE_S1, OUTPUT);
  pinMode(PIN_MUX_FILE_S2, OUTPUT);
  pinMode(PIN_MUX_FILE_S3, OUTPUT);

  pinMode(PIN_LIM_X, INPUT_PULLUP);
  pinMode(PIN_LIM_Y, INPUT_PULLUP);
  
  pinMode(PIN_MAGNET, OUTPUT);

  digitalWrite(PIN_EN_A, HIGH); // Ensure motors are off
  digitalWrite(PIN_EN_B, HIGH);
  motorsEnabled = false;

  digitalWrite(PIN_MAGNET, LOW); // Ensure magnet is off
  magnetUp = false;
  
  home();

  currentTime = millis();
  currentTimeMicros = micros();
  motorTimer = currentTimeMicros;
  telemetryTimer = currentTime;
  executionTimer = currentTime;
}

void loop() {
  currentTime = millis();
  currentTimeMicros = micros();
  
  if (currentTimeMicros >= motorTimer) {
    targetDistanceA = targetPosA - motorPosA;
    targetDistanceB = targetPosB - motorPosB;
    tempAStep = (targetDistanceA != 0);
    tempBStep = (targetDistanceB != 0);

    if (tempAStep or tempBStep) {
      step(tempAStep, tempBStep, targetDistanceA > 0, targetDistanceB > 0, true);
    } else if (count > 0) { // We're finished and there's another command, flag for execution immediately
      executionTimer = millis();
    }
    
    motorTimer += motorIntervalMicros;
  }

  else if (currentTime >= executionTimer) {
    // TODO: Implement idle position
    if (count > 0) {
      if (!motorsEnabled) {
        digitalWrite(PIN_EN_A, LOW); // Enable motors
        digitalWrite(PIN_EN_B, LOW);
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
    } else { // No commands, idle state
      if (motorsEnabled && targetDistanceA == 0 && targetDistanceB == 0) {
        digitalWrite(PIN_EN_A, HIGH);
        digitalWrite(PIN_EN_B, HIGH);
        digitalWrite(PIN_MAGNET, LOW);
        motorsEnabled = false;
        magnetUp = false;
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

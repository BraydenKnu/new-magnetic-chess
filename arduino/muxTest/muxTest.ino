
#define BIT0 0x01
#define BIT1 0x02
#define BIT2 0x04
#define BIT3 0x08
#define BIT4 0x10
#define BIT5 0x20
#define BIT6 0x40
#define BIT7 0x80

#define SERIAL_BAUD_RATE 115200

#define PIN_MUX_SIG A1
#define PIN_MUX_FILE_S0 A5
#define PIN_MUX_FILE_S1 A4
#define PIN_MUX_FILE_S2 A3
#define PIN_MUX_FILE_S3 A2
#define PIN_MUX_RANK_S0 2
#define PIN_MUX_RANK_S1 3
#define PIN_MUX_RANK_S2 4

bool reedSwitchValues[12][8];

bool tempButtonValue;
void updateSwitchesAndButtons() {
  int column = 0;
  int row = 0;
  for (int column = 0; column < 12; column++) {
    // set the PIN_MUX_FILE_S0 through PIN_MUX_FILE_S3 input pins correctly to select the correct column.
    digitalWrite(PIN_MUX_FILE_S0, (column & BIT0) == BIT0);
    digitalWrite(PIN_MUX_FILE_S1, (column & BIT1) == BIT1);
    digitalWrite(PIN_MUX_FILE_S2, (column & BIT2) == BIT2);
    digitalWrite(PIN_MUX_FILE_S3, (column & BIT3) == BIT3);
    for (int row = 0; row < 8; row++) {
      // set the PIN_MUX_RANK_S0 through PIN_MUX_RANK_S2 input pins correctly to select the correct row.
      digitalWrite(PIN_MUX_RANK_S0, (row & BIT0) == BIT0);
      digitalWrite(PIN_MUX_RANK_S1, (row & BIT1) == BIT1);
      digitalWrite(PIN_MUX_RANK_S2, (row & BIT2) == BIT2);
      delayMicroseconds(20);
      reedSwitchValues[column][row] = (digitalRead(PIN_MUX_SIG) == LOW); // Read reed switches
    }
  }
}

void printSwitches() {
  for (int row = 0; row < 8; row++) {
    for (int column = 0; column < 12; column++) {
      Serial.print(reedSwitchValues[column][row] ? '0' : '1'); // Read reed switches
    }
    Serial.println();
  }
  Serial.println();
}

void setup() {
  Serial.begin(SERIAL_BAUD_RATE);

  pinMode(PIN_MUX_SIG, INPUT_PULLUP);

  pinMode(PIN_MUX_RANK_S0, OUTPUT);
  pinMode(PIN_MUX_RANK_S1, OUTPUT);
  pinMode(PIN_MUX_RANK_S2, OUTPUT);
  pinMode(PIN_MUX_FILE_S0, OUTPUT);
  pinMode(PIN_MUX_FILE_S1, OUTPUT);
  pinMode(PIN_MUX_FILE_S2, OUTPUT);
  pinMode(PIN_MUX_FILE_S3, OUTPUT);
}

void loop() {
  delay(1000);
  updateSwitchesAndButtons();
  printSwitches();
}

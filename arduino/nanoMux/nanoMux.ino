
#define BIT0 0x01
#define BIT1 0x02
#define BIT2 0x04
#define BIT3 0x08
#define BIT4 0x10
#define BIT5 0x20
#define BIT6 0x40
#define BIT7 0x80

#define PIN_MUX_IN_S0 A0
#define PIN_MUX_IN_S1 A1
#define PIN_MUX_IN_S2 A2
#define PIN_MUX_IN_S3 A3

#define PIN_MUX_OUT_0 A4
#define PIN_MUX_OUT_1 A5
#define PIN_MUX_OUT_2 2
#define PIN_MUX_OUT_3 3
#define PIN_MUX_OUT_4 4
#define PIN_MUX_OUT_5 5
#define PIN_MUX_OUT_6 6
#define PIN_MUX_OUT_7 7
#define PIN_MUX_OUT_8 8
#define PIN_MUX_OUT_9 9
#define PIN_MUX_OUT_10 10
#define PIN_MUX_OUT_11 11

int outputs[] = {
    PIN_MUX_OUT_0,
    PIN_MUX_OUT_1,
    PIN_MUX_OUT_2,
    PIN_MUX_OUT_3,
    PIN_MUX_OUT_4,
    PIN_MUX_OUT_5,
    PIN_MUX_OUT_6,
    PIN_MUX_OUT_7,
    PIN_MUX_OUT_8,
    PIN_MUX_OUT_9,
    PIN_MUX_OUT_10,
    PIN_MUX_OUT_11
};

int oldInSwitchNumber = 0;
int inSwitchNumber = 0;
int in0 = 0;
int in1 = 0;
int in2 = 0;
int in3 = 0;
int getInSwitchNumber() {
    in0 = digitalRead(PIN_MUX_IN_S0) == HIGH;
    in1 = digitalRead(PIN_MUX_IN_S1) == HIGH;
    in2 = digitalRead(PIN_MUX_IN_S2) == HIGH;
    in3 = digitalRead(PIN_MUX_IN_S3) == HIGH;

    inSwitchNumber = 8*in3 + 4*in2 + 2*in1 + in0;
}

void updateOutputs() {
    if (inSwitchNumber != oldInSwitchNumber && inSwitchNumber < 12) {
        digitalWrite(outputs[oldInSwitchNumber], LOW);
        digitalWrite(outputs[inSwitchNumber], HIGH);

        oldInSwitchNumber = inSwitchNumber;
    }
}

void setup() {    
  pinMode(PIN_MUX_IN_S0, INPUT);
  pinMode(PIN_MUX_IN_S1, INPUT);
  pinMode(PIN_MUX_IN_S2, INPUT);
  pinMode(PIN_MUX_IN_S3, INPUT);

  pinMode(PIN_MUX_OUT_0, OUTPUT);
  pinMode(PIN_MUX_OUT_1, OUTPUT);
  pinMode(PIN_MUX_OUT_2, OUTPUT);
  pinMode(PIN_MUX_OUT_3, OUTPUT);
  pinMode(PIN_MUX_OUT_4, OUTPUT);
  pinMode(PIN_MUX_OUT_5, OUTPUT);
  pinMode(PIN_MUX_OUT_6, OUTPUT);
  pinMode(PIN_MUX_OUT_7, OUTPUT);
  pinMode(PIN_MUX_OUT_8, OUTPUT);
  pinMode(PIN_MUX_OUT_9, OUTPUT);
  pinMode(PIN_MUX_OUT_10, OUTPUT);
  pinMode(PIN_MUX_OUT_11, OUTPUT);

  digitalWrite(PIN_MUX_OUT_0, HIGH);
 }

void loop() {
    getInSwitchNumber();
    updateOutputs();
}

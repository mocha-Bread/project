#include <SoftwareSerial.h>
#include <Stepper.h>

// SoftwareSerial keypadSerial(12, 13); // RX, TX pins
// #define RELAY_PIN 4
#define SCL_PIN 10
#define SDO_PIN 11
// pinMode(SDO_PIN, INPUT);
// pinMode(SDO_PIN, INPUT);
const int STEP_PIN = 7;
const int DIR_PIN = 6;
const int ENA_PIN = 5;

const int TRIG_PIN = 8;  // 초음파 센서의 트리거 핀
const int ECHO_PIN = 9;  // 초음파 센서의 에코 핀

byte Key;
unsigned long lastKeyPressTime = 0;
const unsigned long debounceDelay = 300;
const unsigned long longPressDuration = 2000; // 2 seconds
bool isLongPressing = false;
unsigned long longPressStartTime = 0;
String perf_loc = "";  // perf_loc 변수 선언

void setup() {
  Serial.begin(9600);
  keypadSerial.begin(9600);

  pinMode(SCL_PIN, OUTPUT);
  pinMode(SDO_PIN, INPUT);

  pinMode(ENA_PIN, OUTPUT);
  digitalWrite(ENA_PIN, HIGH);

  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);

  pinMode(TRIG_PIN, OUTPUT); // 초음파 센서의 핀 모드 설정
  pinMode(ECHO_PIN, INPUT);

  pinMode(RELAY_PIN, OUTPUT);  // 릴레이 핀을 출력 모드로 설정
  digitalWrite(RELAY_PIN, LOW);  // 초기에 릴레이를 꺼둡니다

  Serial.println("Setup completed. Ready to receive commands.");
}

void loop() {
  handleKeypad();
  handleMotorRotation();
  delay(100);
  if (perf_loc.length() > 0) {
    Serial.print("Received perf_loc value: ");
    Serial.println(perf_loc);
  }
}

void handleKeypad() {
  static char code[4] = {'-', '-', '-', '-'};
  static int currentIndex = 0;
  static bool inputBlocked = false;

  Key = Read_Keypad();

  if (Key) {
    unsigned long currentMillis = millis();

    if (currentMillis - lastKeyPressTime >= debounceDelay) {
      lastKeyPressTime = currentMillis;

      if (inputBlocked) {
        if (Key == 8) {
          inputBlocked = false;
          currentIndex = 0;
          for (int i = 0; i < 4; i++) {  // code 배열 초기화
            code[i] = '-';
          }
          Serial.println("Ready to receive new input");
        }
      } else {
        if (currentIndex < 4) {
          code[currentIndex] = Key + '0';
          Serial.print("Input: ");
          Serial.println(Key);
          currentIndex++;

          if (currentIndex == 4) {
            int value = 0;
            for (int i = 0; i < currentIndex; i++) {
              value = value * 10 + (code[i] - '0');
            }
            keypadSerial.println(value);
            Serial.print("Sent keypad data: ");
            Serial.println(value);

            inputBlocked = true;
          }
        }
      }
    }
  }

  unsigned long startTime = millis();
  perf_loc = "";  // Reset the string

  while (millis() - startTime < 60) {  // 60ms 동안 ESP32로부터의 데이터 수신 대기. 딜레이보다 약간 더 긴 시간 설정
    while (keypadSerial.available()) {
      char c = keypadSerial.read();
      perf_loc += c;
    }
  }

  // Display the perf_loc value from ESP32 on the Serial Monitor
  if (perf_loc.length() > 0) {
    Serial.print("Received perf_loc value: ");
  }
}

void handleMotorRotation() {
  if (perf_loc.length() > 0) {
    int val = perf_loc.toInt();

    int degrees[] = {0, 60, 120, 180, 240, 300};
    if (val >= 1 && val <= 6) {
      rotateMotor(degrees[val]);
      Serial.println("Waiting for an object to approach the ultrasonic sensor...");

      // 초음파 센서가 10cm 이내의 거리를 감지할 때까지 기다림
      while (readUltrasonicDistance() > 10) {
        delay(100);
      }
      digitalWrite(RELAY_PIN, HIGH);
      delay(2000);  // 2초 동안 모터를 작동시킵니다.
      digitalWrite(RELAY_PIN, LOW);  // 릴레이를 꺼서 모터를 정지시킵니다

      Serial.println("Object detected! Returning motor to the original position.");
      rotateMotor(-degrees[val]);

      Serial.println("Motor returned to the original position.");
    } else {
      Serial.println("Invalid input. Please enter a value between 1 and 6.");
    }

    while (Serial.available()) {
      Serial.read();
    }
    perf_loc = "";
  }
}

byte Read_Keypad() {
  byte Key_State = 0;
  static byte i = 0;
  for (byte Count = 1; Count <= 11; Count++) {
    digitalWrite(SCL_PIN, LOW);

    if (!digitalRead(SDO_PIN))
      Key_State = Count;

    digitalWrite(SCL_PIN, HIGH);
  }

  if (i == 0 && Key_State == 11) {
    // 시리얼 창에 11이 표시될 때 1234를 keypadSerial을 통해 ESP로 한 번만 전송
    keypadSerial.println(1234);
    Serial.println("Sent keypad data: 1234");
    i++; // i를 1로 증가시킴
  } else if (i > 0 && i <= 6) {
    // i가 1 이상 6 이하인 경우, 1234부터 1235, 1236, ... 순차적으로 보내기
    int value = 1234 + i;
    keypadSerial.println(value);
    // Serial.print("Sent keypad data: ");
    // Serial.println(value);
    i++; // i를 1씩 증가시킴
    
    if (i > 6) {
      // i가 6을 초과하면 다시 0으로 초기화 (원하는 범위에서 계속 반복)
      i = 1;
    }
  }

  return Key_State;
}

void rotateMotor(int angle) {
  int totalSteps = map(angle, 0, 360, 0, 2048);

  if (angle > 0) {
    digitalWrite(DIR_PIN, HIGH);
  } else {
    digitalWrite(DIR_PIN, LOW);
  }

  for (int i = 0; i < abs(totalSteps); i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(500);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(500);
  }
  delay(1000);
}

long readUltrasonicDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH);
  return duration * 0.0344 / 2;
}

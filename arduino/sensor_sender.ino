#include <Wire.h>
#include <SoftwareSerial.h>

// GPS
SoftwareSerial gpsSerial(4, 3);  
// GPS TX -> D4
// GPS RX اختياري -> D3

// MPU6050
#define MPU_ADDR 0x68

// Pins
#define BUZZER_PIN 12
#define TRIG_PIN 6
#define ECHO_PIN 7
#define VIB_PIN 5

bool buzzerState = false;
bool vibState = false;
bool autoAlarm = true;

int alarmDistance = 50;   // cm
float distanceCm = -1;

unsigned long lastPrint = 0;
unsigned long lastUltra = 0;

int16_t ax, ay, az, tempRaw, gx, gy, gz;

String command = "";

// GPS parsing
char gpsBuffer[120];
int gpsIdx = 0;
float gpsLat = 0.0;
float gpsLon = 0.0;
bool gpsFix = false;

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(9600);

  Wire.begin();

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(VIB_PIN, OUTPUT);

  digitalWrite(BUZZER_PIN, LOW);
  analogWrite(VIB_PIN, 0);

  // Wake up MPU6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  byte error = Wire.endTransmission(true);

  if (error == 0) {
    Serial.println("{\"status\":\"ready\",\"mpu\":true}");
  } else {
    Serial.println("{\"status\":\"ready\",\"mpu\":false}");
  }
}

void loop() {
  readSerialCommand();
  processGPS();

  // Read ultrasonic كل 100ms
  if (millis() - lastUltra >= 100) {
    lastUltra = millis();
    distanceCm = readUltrasonicCM();

    if (autoAlarm) {
      if (distanceCm > 0 && distanceCm <= alarmDistance) {
        buzzerState = true;
        vibState = true;
      } else {
        buzzerState = false;
        vibState = false;
      }
    }

    applyOutputs();
  }

  // عرض القراءات بصيغة JSON كل ثانية
  if (millis() - lastPrint >= 1000) {
    lastPrint = millis();
    sendJSON();
  }
}

// ================= GPS Parsing =================
void processGPS() {
  while (gpsSerial.available()) {
    char c = gpsSerial.read();
    
    if (c == '\n') {
      gpsBuffer[gpsIdx] = '\0';
      if (strncmp(gpsBuffer, "$GPRMC", 6) == 0 || strncmp(gpsBuffer, "$GNRMC", 6) == 0) {
        parseGPRMC();
      }
      gpsIdx = 0;
    } else if (c != '\r' && gpsIdx < 118) {
      gpsBuffer[gpsIdx++] = c;
    }
  }
}

void parseGPRMC() {
  char buf[120];
  strncpy(buf, gpsBuffer, 119);
  buf[119] = '\0';
  
  char* fields[13];
  int fieldCount = 0;
  char* token = strtok(buf, ",");
  
  while (token != NULL && fieldCount < 13) {
    fields[fieldCount++] = token;
    token = strtok(NULL, ",");
  }
  
  if (fieldCount < 7) return;
  if (fields[2][0] != 'A') {
    gpsFix = false;
    return;
  }
  
  float rawLat = atof(fields[3]);
  int latDeg = (int)(rawLat / 100);
  float latMin = rawLat - latDeg * 100.0;
  gpsLat = latDeg + latMin / 60.0;
  if (fields[4][0] == 'S') gpsLat = -gpsLat;
  
  float rawLon = atof(fields[5]);
  int lonDeg = (int)(rawLon / 100);
  float lonMin = rawLon - lonDeg * 100.0;
  gpsLon = lonDeg + lonMin / 60.0;
  if (fields[6][0] == 'W') gpsLon = -gpsLon;
  
  gpsFix = true;
}

// ================= Serial Control =================
void readSerialCommand() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      command.trim();
      if (command.length() > 0) {
        handleCommand(command);
        command = "";
      }
    } else {
      command += c;
    }
  }
}

void handleCommand(String cmd) {
  cmd.trim();
  cmd.toLowerCase();

  if (cmd == "b1") {
    buzzerState = true;
    autoAlarm = false;
    Serial.println("{\"cmd\":\"b1\",\"ok\":true}");
  } 
  else if (cmd == "b0") {
    buzzerState = false;
    autoAlarm = false;
    Serial.println("{\"cmd\":\"b0\",\"ok\":true}");
  } 
  else if (cmd == "v1") {
    vibState = true;
    autoAlarm = false;
    Serial.println("{\"cmd\":\"v1\",\"ok\":true}");
  } 
  else if (cmd == "v0") {
    vibState = false;
    autoAlarm = false;
    Serial.println("{\"cmd\":\"v0\",\"ok\":true}");
  } 
  else if (cmd == "a1") {
    autoAlarm = true;
    Serial.println("{\"cmd\":\"a1\",\"ok\":true}");
  } 
  else if (cmd == "a0") {
    autoAlarm = false;
    Serial.println("{\"cmd\":\"a0\",\"ok\":true}");
  } 
  else if (cmd.startsWith("d")) {
    int value = cmd.substring(1).toInt();
    if (value > 0) {
      alarmDistance = value;
      Serial.println("{\"cmd\":\"d\",\"val\":" + String(alarmDistance) + ",\"ok\":true}");
    }
  }
  else if (cmd == "alert") {
    buzzerState = true;
    vibState = true;
    autoAlarm = false;
    Serial.println("{\"cmd\":\"alert\",\"ok\":true}");
  }
  else if (cmd == "stop") {
    buzzerState = false;
    vibState = false;
    autoAlarm = false;
    Serial.println("{\"cmd\":\"stop\",\"ok\":true}");
  }
  else if (cmd == "palert") {
    // Intermittent pothole alert: 3 short bursts
    autoAlarm = false;
    for (int i = 0; i < 3; i++) {
      digitalWrite(BUZZER_PIN, HIGH);
      analogWrite(VIB_PIN, 255);
      delay(200);
      digitalWrite(BUZZER_PIN, LOW);
      analogWrite(VIB_PIN, 0);
      delay(150);
    }
    buzzerState = false;
    vibState = false;
    Serial.println("{\"cmd\":\"palert\",\"ok\":true}");
  }
  else if (cmd == "r") {
    sendJSON();
  } 
  else {
    Serial.println("{\"cmd\":\"unknown\",\"ok\":false}");
  }

  applyOutputs();
}

// ================= Outputs =================
void applyOutputs() {
  digitalWrite(BUZZER_PIN, buzzerState ? HIGH : LOW);
  analogWrite(VIB_PIN, vibState ? 255 : 0);
}

// ================= Ultrasonic =================
float readUltrasonicCM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 25000UL);

  if (duration == 0) {
    return -1;
  }

  return duration / 58.0;
}

// ================= MPU6050 =================
bool readMPU6050() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);

  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  Wire.requestFrom(MPU_ADDR, 14, true);

  if (Wire.available() < 14) {
    return false;
  }

  ax = Wire.read() << 8 | Wire.read();
  ay = Wire.read() << 8 | Wire.read();
  az = Wire.read() << 8 | Wire.read();

  tempRaw = Wire.read() << 8 | Wire.read();

  gx = Wire.read() << 8 | Wire.read();
  gy = Wire.read() << 8 | Wire.read();
  gz = Wire.read() << 8 | Wire.read();

  return true;
}

// ================= Print JSON Data =================
void sendJSON() {
  readMPU6050();

  Serial.print("{\"d\":");
  Serial.print(distanceCm, 1);
  
  Serial.print(",\"ax\":");
  Serial.print(ax);
  Serial.print(",\"ay\":");
  Serial.print(ay);
  Serial.print(",\"az\":");
  Serial.print(az);
  
  Serial.print(",\"gx\":");
  Serial.print(gx);
  Serial.print(",\"gy\":");
  Serial.print(gy);
  Serial.print(",\"gz\":");
  Serial.print(gz);
  
  Serial.print(",\"lat\":");
  Serial.print(gpsLat, 6);
  Serial.print(",\"lon\":");
  Serial.print(gpsLon, 6);
  Serial.print(",\"gps\":");
  Serial.print(gpsFix ? "true" : "false");
  
  Serial.print(",\"buz\":");
  Serial.print(buzzerState ? 1 : 0);
  Serial.print(",\"vib\":");
  Serial.print(vibState ? 1 : 0);
  Serial.print(",\"auto\":");
  Serial.print(autoAlarm ? 1 : 0);
  Serial.print(",\"ad\":");
  Serial.print(alarmDistance);
  
  Serial.println("}");
}

// WiFi Setup
#include <ESP8266WiFi.h>
const char* ssid = "";
const char* password = "";

const int MotionTimeoutLimit = 15; 

// Motion Sensor Setup
int pirPin = D1;
int pirValue;

// Pi Setup
int piPowerPin = D2;
int piPin = D5;

// Variables
int motionTimeout = 0; // Counts up when no motion
bool piBooted = false; // Is the Pi Booted

void setup() {
  Serial.begin(115200);
  Serial.println("Starting Up");
  WiFi.begin(ssid, password);
  pinMode(LED_BUILTIN, OUTPUT);

  pinMode(pirPin, INPUT);
  delay(20000);
  Serial.println("Sensor Active");

  pinMode(piPowerPin, OUTPUT); // connect Pi power output
  pinMode(piPin, INPUT); // detects if pi is booted

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("WiFi Connected!");
  Serial.println(WiFi.localIP());
  WiFi.setAutoReconnect(true);

}

void loop() {

  bool motion = detectMotion();

  if (!motion) { // no motion detected, wait and restart loop
    digitalWrite(LED_BUILTIN, LOW);
    motionTimeout += 1;
    delay(1000);
    if (motionTimeout > MotionTimeoutLimit) {
      shutdownPi();
    }
    return;  
  }
  motionTimeout = 0;
  bootPi();
  delay(500);
}

bool detectMotion() {  // detects motion from PIR
  pirValue = digitalRead(pirPin);

  if (pirValue == HIGH) {
    Serial.println("Motion Detected!");
    return true;
  }
  return false;
}

void bootPi() { // Boots up PI safely
  
  Serial.println("Pi Booting");
  digitalWrite(piPowerPin, HIGH); // Send power to Pi
  while(!detectPi()) { // Tries to find Pi, on fail waits and tries again
    delay(500);
  }

  piBooted = true;
  Serial.println("Pi Booting Finished");
}

bool detectPi() {
  if (digitalRead(piPin) == HIGH) {
    return true;
  }
  return false;
}

void shutdownPi() { // Shuts down PI safely
  Serial.println("Pi Shutting Down");
  piBooted = false;
  while(detectPi()) { // waits for Pi to shut itself down before removing power
    delay(500);
  }
  digitalWrite(piPowerPin, LOW);

  Serial.println("Pi Shut Down");
  // to solve - send a shutdown signal to pi, so it can get ready to shutdown.
}
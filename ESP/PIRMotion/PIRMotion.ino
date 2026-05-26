// Motion Sensor Setup
int pirPin = D1;
int pirValue;

void setup() {
  Serial.begin(115200);
  pinMode(pirPin, INPUT);
  Serial.println("Sensor Active");
  delay(20000);
}

void loop() {
  pirValue = digitalRead(pirPin);

  if (pirValue == HIGH) {
    Serial.println("Motion Detected!");
  } else {
    Serial.println("No Motion");
  }

  delay(500);

}

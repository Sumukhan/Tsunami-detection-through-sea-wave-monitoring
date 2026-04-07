#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_LSM303_Accel.h>


const char* ssid = ""; //Network name here
const char* password = ""; //Password of network here

String serverURL = "http://10.141.130.150:5000/data";

Adafruit_LSM303_Accel_Unified accel = Adafruit_LSM303_Accel_Unified(12345);

uint8_t nodeId;
unsigned long lastSend = 0;
const unsigned long INTERVAL = 2000;  // 2 sec
const float ALERT_THRESHOLD = 7.0;    // m/s²

float prev_ax=0, prev_ay=0, prev_az=0;

void setup() {
  Serial.begin(115200);

  // unique node ID
  uint8_t mac[6];
  WiFi.macAddress(mac);
  nodeId = mac[5];

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nConnected to WiFi.");

  if (!accel.begin()) {
    Serial.println("Accel not found!");
    while(true);
  }
}

void loop() {
  unsigned long now = millis();
  if (now - lastSend < INTERVAL) return;
  lastSend = now;

  sensors_event_t event;
  accel.getEvent(&event);

  // remove gravity in Z axis (~9.8)
  float ax = event.acceleration.x;
  float ay = event.acceleration.y;
  float az = event.acceleration.z + 9.81;  // remove g if sensor Z points down

  // delta magnitude
  float delta = sqrt(pow(ax - prev_ax,2) + pow(ay - prev_ay,2) + pow(az - prev_az,2));
  prev_ax = ax; prev_ay = ay; prev_az = az;

  bool alert = (delta >= ALERT_THRESHOLD);

  // Prepare JSON
  String json = "{";
  json += "\"node_id\":" + String(nodeId) + ",";
  json += "\"ax\":" + String(ax,3) + ",";
  json += "\"ay\":" + String(ay,3) + ",";
  json += "\"az\":" + String(az,3) + ",";
  json += "\"alert\":" + String(alert ? "true":"false");
  json += "}";

  // POST
  if(WiFi.status() == WL_CONNECTED){
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type","application/json");
    http.POST(json);
    http.end();
  }

  Serial.printf("Sent node %d | delta: %.2f | alert: %s\n", nodeId, delta, alert?"YES":"NO");
}
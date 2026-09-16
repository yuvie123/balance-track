#include "config.h"
#include "sensors.h"
#include "orientation.h"
#include "logger.h"
#include "web.h"

enum State { IDLE, CALIBRATING, RECORDING, ERROR_STATE };

State state = IDLE;
uint32_t lastSample = 0;
uint32_t recordStart = 0;
uint32_t lastBlink = 0;
bool ledOn = false;
bool hardwareOk = true;

int lastButton = HIGH;
uint32_t lastButtonChange = 0;

const char *stateName() {
  switch (state) {
    case IDLE: return "idle";
    case CALIBRATING: return "calibrating";
    case RECORDING: return "recording";
    default: return "error";
  }
}

bool startRecording() {
  if (state != IDLE) return false;
  sensorsStartCalibration();
  state = CALIBRATING;
  return true;
}

void stopRecording() {
  if (state == ERROR_STATE && hardwareOk) {
    state = IDLE;
    return;
  }
  if (state == CALIBRATING) {
    state = IDLE;
    return;
  }
  if (state != RECORDING) return;
  loggerStop();
  state = IDLE;
}

void checkButton() {
  int reading = digitalRead(PIN_BUTTON);
  if (reading != lastButton && millis() - lastButtonChange > 50) {
    lastButtonChange = millis();
    lastButton = reading;
    if (reading == LOW) {
      if (state == IDLE) startRecording();
      else stopRecording();
    }
  }
}

void updateLed() {
  uint32_t period;
  switch (state) {
    case RECORDING:
      digitalWrite(PIN_LED, HIGH);
      return;
    case CALIBRATING: period = 100; break;
    case ERROR_STATE: period = 250; break;
    default: period = 1000; break;
  }
  if (millis() - lastBlink >= period) {
    lastBlink = millis();
    ledOn = !ledOn;
    digitalWrite(PIN_LED, ledOn);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);

  if (!sensorsBegin() || !loggerBegin()) {
    hardwareOk = false;
    state = ERROR_STATE;
  }
  webBegin();
}

void loop() {
  webHandle();
  checkButton();
  updateLed();

  uint32_t now = millis();
  if (now - lastSample < SAMPLE_INTERVAL_MS) return;
  float dt = (now - lastSample) / 1000.0f;
  lastSample = now;

  if (state == CALIBRATING) {
    sensorsCalibrationStep();
    if (!sensorsCalibrating()) {
      if (loggerStart()) {
        orientationReset();
        recordStart = now;
        state = RECORDING;
      } else {
        state = ERROR_STATE;
      }
    }
    return;
  }

  if (state != RECORDING) return;

  Sample s;
  s.t = now - recordStart;
  sensorsRead(s);
  orientationUpdate(s, dt);

  if (!loggerAdd(s)) {
    Serial.println("storage full, stopping");
    loggerStop();
    state = ERROR_STATE;
  }
}

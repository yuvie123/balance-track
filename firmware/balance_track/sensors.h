#pragma once

#include <Arduino.h>

struct Sample {
  uint32_t t;
  float ax, ay, az;
  float gx, gy, gz;
  float roll, pitch;
  float alt;
};

bool sensorsBegin();
void sensorsRead(Sample &s);
void sensorsStartCalibration();
bool sensorsCalibrating();
void sensorsCalibrationStep();

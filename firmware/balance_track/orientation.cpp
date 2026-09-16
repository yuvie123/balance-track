#include "orientation.h"
#include "config.h"

#include <math.h>

static float roll = 0;
static float pitch = 0;
static bool primed = false;

void orientationReset() {
  roll = 0;
  pitch = 0;
  primed = false;
}

void orientationUpdate(Sample &s, float dt) {
  float accRoll = atan2(s.ay, s.az) * RAD_TO_DEG;
  float accPitch = atan2(-s.ax, sqrt(s.ay * s.ay + s.az * s.az)) * RAD_TO_DEG;

  if (!primed) {
    roll = accRoll;
    pitch = accPitch;
    primed = true;
  } else {
    // gyro handles fast motion, accel pulls it back so drift can't build up
    roll = FILTER_ALPHA * (roll + s.gx * RAD_TO_DEG * dt) + (1.0f - FILTER_ALPHA) * accRoll;
    pitch = FILTER_ALPHA * (pitch + s.gy * RAD_TO_DEG * dt) + (1.0f - FILTER_ALPHA) * accPitch;
  }

  s.roll = roll;
  s.pitch = pitch;
}

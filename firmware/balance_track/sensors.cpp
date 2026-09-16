#include "sensors.h"
#include "config.h"

#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_BMP280.h>

static Adafruit_MPU6050 mpu;
static Adafruit_BMP280 bmp;

static float biasX = 0, biasY = 0, biasZ = 0;
static double sumX = 0, sumY = 0, sumZ = 0;
static uint32_t calCount = 0;
static uint32_t calStart = 0;
static bool calibrating = false;
static float lastAlt = 0;
static uint32_t lastAltRead = 0;

bool sensorsBegin() {
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);

  if (!mpu.begin()) {
    Serial.println("MPU6050 not found");
    return false;
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_44_HZ);

  if (!bmp.begin(0x76) && !bmp.begin(0x77)) {
    Serial.println("BMP280 not found");
    return false;
  }
  bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,
                  Adafruit_BMP280::SAMPLING_X2,
                  Adafruit_BMP280::SAMPLING_X16,
                  Adafruit_BMP280::FILTER_X4,
                  Adafruit_BMP280::STANDBY_MS_63);
  return true;
}

void sensorsRead(Sample &s) {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  s.ax = a.acceleration.x;
  s.ay = a.acceleration.y;
  s.az = a.acceleration.z;
  s.gx = g.gyro.x - biasX;
  s.gy = g.gyro.y - biasY;
  s.gz = g.gyro.z - biasZ;

  // baro is slow to read and altitude barely changes between samples
  if (millis() - lastAltRead >= 100) {
    lastAlt = bmp.readAltitude(SEA_LEVEL_HPA);
    lastAltRead = millis();
  }
  s.alt = lastAlt;
}

void sensorsStartCalibration() {
  sumX = sumY = sumZ = 0;
  calCount = 0;
  calStart = millis();
  calibrating = true;
}

bool sensorsCalibrating() {
  return calibrating;
}

void sensorsCalibrationStep() {
  if (!calibrating) return;

  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  sumX += g.gyro.x;
  sumY += g.gyro.y;
  sumZ += g.gyro.z;
  calCount++;

  if (millis() - calStart >= CALIBRATION_MS && calCount > 0) {
    biasX = sumX / calCount;
    biasY = sumY / calCount;
    biasZ = sumZ / calCount;
    calibrating = false;
    Serial.printf("gyro bias %.4f %.4f %.4f (%u samples)\n", biasX, biasY, biasZ, (unsigned)calCount);
  }
}

#include "logger.h"
#include "config.h"

#include <LittleFS.h>

static Sample buffer[BUFFER_SAMPLES];
static size_t count = 0;
static bool active = false;
static String path;

bool loggerBegin() {
  if (!LittleFS.begin(true)) {
    Serial.println("LittleFS mount failed");
    return false;
  }
  if (!LittleFS.exists(SESSION_DIR)) {
    LittleFS.mkdir(SESSION_DIR);
  }
  return true;
}

size_t loggerFreeBytes() {
  return LittleFS.totalBytes() - LittleFS.usedBytes();
}

static String nextSessionPath() {
  int highest = 0;
  File dir = LittleFS.open(SESSION_DIR);
  File f = dir.openNextFile();
  while (f) {
    String name = f.name();
    if (name.startsWith("s") && name.endsWith(".csv")) {
      int n = name.substring(1, name.length() - 4).toInt();
      if (n > highest) highest = n;
    }
    f = dir.openNextFile();
  }

  char buf[32];
  snprintf(buf, sizeof(buf), SESSION_DIR "/s%03d.csv", highest + 1);
  return String(buf);
}

static bool flush() {
  if (count == 0) return true;

  File f = LittleFS.open(path, FILE_APPEND);
  if (!f) return false;

  char line[160];
  for (size_t i = 0; i < count; i++) {
    const Sample &s = buffer[i];
    int n = snprintf(line, sizeof(line), "%lu,%.3f,%.3f,%.3f,%.4f,%.4f,%.4f,%.2f,%.2f,%.2f\n",
                     (unsigned long)s.t, s.ax, s.ay, s.az, s.gx, s.gy, s.gz, s.roll, s.pitch, s.alt);
    f.write((uint8_t *)line, n);
  }
  f.close();
  count = 0;
  return true;
}

bool loggerStart() {
  if (loggerFreeBytes() < MIN_FREE_BYTES) return false;

  path = nextSessionPath();
  File f = LittleFS.open(path, FILE_WRITE);
  if (!f) return false;
  f.println("t_ms,ax,ay,az,gx,gy,gz,roll,pitch,alt_m");
  f.close();

  count = 0;
  active = true;
  Serial.printf("recording to %s\n", path.c_str());
  return true;
}

bool loggerAdd(const Sample &s) {
  if (!active) return false;

  buffer[count++] = s;
  if (count < BUFFER_SAMPLES) return true;

  if (!flush() || loggerFreeBytes() < MIN_FREE_BYTES) {
    active = false;
    return false;
  }
  return true;
}

void loggerStop() {
  if (!active) return;
  flush();
  active = false;
  Serial.printf("saved %s\n", path.c_str());
}

bool loggerActive() {
  return active;
}

String loggerCurrentName() {
  return path;
}

#include "web.h"
#include "config.h"
#include "logger.h"

#include <WiFi.h>
#include <WebServer.h>
#include <LittleFS.h>

static WebServer server(80);

static bool validName(const String &name) {
  if (!name.startsWith("s") || !name.endsWith(".csv")) return false;
  if (name.indexOf('/') >= 0 || name.indexOf("..") >= 0) return false;
  return true;
}

static void handleStatus() {
  String json = "{";
  json += "\"state\":\"" + String(stateName()) + "\",";
  json += "\"sample_hz\":" + String(1000 / SAMPLE_INTERVAL_MS) + ",";
  json += "\"free_bytes\":" + String(loggerFreeBytes()) + ",";
  json += "\"current\":\"" + (loggerActive() ? loggerCurrentName() : String("")) + "\"";
  json += "}";
  server.send(200, "application/json", json);
}

static void handleList() {
  String json = "[";
  File dir = LittleFS.open(SESSION_DIR);
  File f = dir.openNextFile();
  bool first = true;
  while (f) {
    if (!first) json += ",";
    json += "{\"name\":\"" + String(f.name()) + "\",\"size\":" + String(f.size()) + "}";
    first = false;
    f = dir.openNextFile();
  }
  json += "]";
  server.send(200, "application/json", json);
}

static void handleSession() {
  String uri = server.uri();
  String name = uri.substring(String("/sessions/").length());
  if (!validName(name)) {
    server.send(400, "text/plain", "bad session name");
    return;
  }

  String path = String(SESSION_DIR) + "/" + name;
  if (!LittleFS.exists(path)) {
    server.send(404, "text/plain", "not found");
    return;
  }

  if (server.method() == HTTP_DELETE) {
    if (loggerActive() && loggerCurrentName() == path) {
      server.send(409, "text/plain", "session is recording");
      return;
    }
    LittleFS.remove(path);
    server.send(200, "text/plain", "deleted");
    return;
  }

  File f = LittleFS.open(path, FILE_READ);
  server.streamFile(f, "text/csv");
  f.close();
}

static void handleStart() {
  if (startRecording()) {
    server.send(200, "text/plain", "ok");
  } else {
    server.send(409, "text/plain", "could not start");
  }
}

static void handleStop() {
  stopRecording();
  server.send(200, "text/plain", "ok");
}

void webBegin() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.print("AP up at ");
  Serial.println(WiFi.softAPIP());

  server.on("/status", HTTP_GET, handleStatus);
  server.on("/sessions", HTTP_GET, handleList);
  server.on("/record/start", HTTP_POST, handleStart);
  server.on("/record/stop", HTTP_POST, handleStop);
  server.onNotFound([]() {
    if (server.uri().startsWith("/sessions/")) {
      handleSession();
    } else {
      server.send(404, "text/plain", "not found");
    }
  });
  server.begin();
}

void webHandle() {
  server.handleClient();
}

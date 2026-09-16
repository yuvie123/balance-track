#pragma once

#include <Arduino.h>

void webBegin();
void webHandle();

bool startRecording();
void stopRecording();
const char *stateName();

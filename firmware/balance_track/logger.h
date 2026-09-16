#pragma once

#include "sensors.h"

bool loggerBegin();
bool loggerStart();
bool loggerAdd(const Sample &s);
void loggerStop();
bool loggerActive();
String loggerCurrentName();
size_t loggerFreeBytes();

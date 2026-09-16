# Firmware

ESP32 sketch for the sensor insole. Built with the Arduino IDE.

## Setup

1. Boards Manager: install **esp32 by Espressif** (2.x or 3.x both work).
2. Library Manager: install **Adafruit MPU6050**, **Adafruit BMP280 Library** and **Adafruit Unified Sensor**.
3. Open `balance_track/balance_track.ino`, pick **ESP32 Dev Module**, upload.

Serial monitor at 115200 shows sensor detection and the AP address.

## Wiring

| Part | Pin | ESP32 |
| --- | --- | --- |
| MPU6050 | VCC / GND | 3V3 / GND |
| MPU6050 | SDA / SCL | GPIO 21 / GPIO 22 |
| BMP280 | VCC / GND | 3V3 / GND |
| BMP280 | SDA / SCL | GPIO 21 / GPIO 22 |
| Button | one side | GPIO 4 |
| Button | other side | GND |
| LED | built in | GPIO 2 |

Both sensors share the I2C bus (MPU6050 at 0x68, BMP280 at 0x76 or 0x77).

Mount the MPU6050 flat under the midfoot with the x axis pointing at the toes and the chip facing up. The analysis treats positive roll as the medial side dropping. If the board ends up rotated 180 degrees, roll flips sign, so check a session with `balancetrack simulate --profile normal` for comparison.

## LED

| Pattern | Meaning |
| --- | --- |
| slow blink | idle, ready |
| very fast blink | calibrating gyro, keep still (2 s) |
| solid | recording |
| medium blink | error (sensor missing or storage full), press the button to clear a storage error |

## HTTP API

The insole runs an access point `BalanceTrack` at `192.168.4.1`.

| Method | Path | |
| --- | --- | --- |
| GET | `/status` | state, sample rate, free space |
| GET | `/sessions` | list of recorded sessions |
| GET | `/sessions/s001.csv` | download a session |
| DELETE | `/sessions/s001.csv` | delete a session |
| POST | `/record/start` | start recording (same as the button) |
| POST | `/record/stop` | stop recording |

## CSV format

```
t_ms,ax,ay,az,gx,gy,gz,roll,pitch,alt_m
```

Acceleration in m/s^2, gyro in rad/s (bias removed), roll and pitch in degrees, altitude in metres.

Each row is about 65 bytes, so 100 Hz works out to roughly 400 KB a minute. The default partition scheme only leaves ~1.5 MB for files (about 3 minutes), so under Tools > Partition Scheme pick **No OTA (2MB APP/2MB SPIFFS)** for around 5 minutes of recording. Fetch with `--delete` to free space between sessions. If flash fills up mid walk the file is closed and the LED switches to the error blink.

# Insole code (firmware)

This is the code that runs on the tiny computer (ESP32) inside the insole. It does three things:

1. reads the motion and pressure sensors 100 times a second
2. saves each walk as a file
3. creates a WiFi network so your laptop can download the walks

## Putting the code on the ESP32

You'll need the free [Arduino IDE](https://www.arduino.cc/en/software).

1. **Add ESP32 support:** go to Tools > Board > Boards Manager, search **esp32** and install **esp32 by Espressif**.
2. **Add the sensor libraries:** go to Tools > Manage Libraries and install **Adafruit MPU6050**, **Adafruit BMP280 Library** and **Adafruit Unified Sensor**.
3. **Open the code:** open `balance_track/balance_track.ino`.
4. **Pick the board:** Tools > Board > **ESP32 Dev Module**.
5. **Make room for recordings:** Tools > Partition Scheme > **No OTA (2MB APP/2MB SPIFFS)**. Without this, the insole can only hold about 3 minutes of walking.
6. Plug in the ESP32 and click **Upload**.

To check it's working, open Tools > Serial Monitor at 115200 baud. It tells you if either sensor isn't found.

## Wiring

Both sensors connect to the same two data pins, so they share wires.

| Connect this | to this ESP32 pin |
| --- | --- |
| MPU6050 VCC and BMP280 VCC | 3V3 |
| MPU6050 GND and BMP280 GND | GND |
| MPU6050 SDA and BMP280 SDA | GPIO 21 |
| MPU6050 SCL and BMP280 SCL | GPIO 22 |
| button, one leg | GPIO 4 |
| button, other leg | GND |

The status light is the small LED already built into the ESP32.

**Sensor placement:** tape the MPU6050 flat under the middle of the foot, chip facing up, with the arrow marked **X** on the board pointing toward the toes. If it's turned around, the program will mix up "rolling inward" and "rolling outward".

## What the light means

| Light | Meaning |
| --- | --- |
| slow blink | ready |
| very fast blink | getting ready, keep your foot still (2 seconds) |
| on solid | recording |
| medium blink | something's wrong: a sensor isn't connected, or memory is full. Press the button to clear a full-memory error. |

## Storage

The insole holds about 5 minutes of walking. To free up space, download walks with `balancetrack fetch --delete`, which deletes them from the insole once they're saved on your laptop. If memory fills up during a walk, the recording is saved up to that point and the light switches to the medium blink.

## For developers

**WiFi:** network `BalanceTrack`, password `insole123` (change it in `config.h`). The insole's address is `192.168.4.1`.

| Request | What it does |
| --- | --- |
| `GET /status` | whether it's recording, and how much space is left |
| `GET /sessions` | list of saved walks |
| `GET /sessions/s001.csv` | download a walk |
| `DELETE /sessions/s001.csv` | delete a walk |
| `POST /record/start` | start recording (same as pressing the button) |
| `POST /record/stop` | stop recording |

**File format:** each walk is a CSV with these columns:

```
t_ms,ax,ay,az,gx,gy,gz,roll,pitch,alt_m
```

`t_ms` is time in milliseconds. `ax/ay/az` is acceleration (m/s^2). `gx/gy/gz` is rotation speed (rad/s). `roll/pitch` is tilt (degrees). `alt_m` is altitude (metres).

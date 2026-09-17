# Balance Track

A self-powered sensor insole for people with vestibular balance disorders, and the software that turns a walk into a custom 3D printed insole.

I built this between September 2025 and April 2026 and am only putting it on GitHub now, in September 2026. The code was cleaned up and reorganized for this upload, so it won't match the original prototype line for line.

Balance therapy usually runs $100-200 per clinical session. The idea here is a one-time ~$121 device: wear the sensor insole for a few minutes of walking, look at how the foot actually moves, then print a corrective insole with support where the instability shows up.

```
scan                      read                              print
ESP32 insole  --wifi-->   step detection, gait features  -->  thickness map -> STL -> PLA/TPU insole
```

## How it works

**Scan.** An ESP32 in the insole reads an MPU6050 (accel + gyro) and a BMP280 (barometric altitude) over I2C at 100 Hz. Sampling runs off `millis()` instead of `delay()` so timing stays even while the web server is running. Roll and pitch come from a complementary filter, so the accelerometer corrects gyro drift on every sample instead of letting it build up over a walk. Samples are buffered in RAM and written to flash in batches of 200, because writing every row was slow enough to throw off the spacing between readings.

**Read.** After the walk the insole hosts a WiFi network and the CSV gets pulled onto a laptop. The analysis:

- finds heel strikes as peaks in acceleration magnitude, with a 0.35 s refractory window so the bounce right after a strike isn't counted as another step
- splits the walk into strides and measures stride time, stance roll (foot rolling in or out), roll variability, pitch range and heel impact
- compares those against expected values for the person's height and weight

**Print.** Anything that's off by more than 1.5 standard deviations adds support to a 2D thickness grid shaped like the person's insole (sized from shoe size):

| What the data shows | What gets added |
| --- | --- |
| foot rolls inward during stance | medial arch post and heel wedge |
| foot rolls outward | lateral wedge |
| roll or stride timing varies a lot step to step | raised heel cup and a stiffer base |
| hard heel strike | heel pad |

The grid is turned into a closed mesh (two triangles per cell on top and bottom, walls around the outline) and written as a binary STL. Every mesh is checked to be watertight before it's saved.

## Repo layout

```
firmware/balance_track/   ESP32 sketch (Arduino IDE)
analysis/balancetrack/    Python package + CLI
analysis/tests/           pytest suite, runs on simulated walks
examples/                 sample session to try the pipeline without hardware
```

## Hardware

- ESP32 DevKit v1
- MPU6050 breakout
- BMP280 breakout
- momentary push button
- 3.7V LiPo + TP4056 charger (plus the piezo harvesting pads if you're building the self-powered version)
- PLA for a rigid insole, TPU 95A if you want it softer

Wiring and flashing are in [firmware/README.md](firmware/README.md).

## Running it

Setup (Python 3.8+):

```
python -m venv .venv
.venv\Scripts\activate          # source .venv/bin/activate on mac/linux
pip install -e "analysis[dev]"
```

Try it without the insole:

```
balancetrack run examples/sample_session.csv --height 175 --weight 70 --shoe 10 --foot left --both -o out
```

With the real insole:

1. Press the button, wait for the very fast blink to stop (gyro calibration, keep the foot still), walk for 2-3 minutes, press again.
2. Connect to the `BalanceTrack` WiFi network (password in `firmware/balance_track/config.h`).
3. `balancetrack fetch -o data` to grab the latest session (`--all` for everything, `--delete` to clear the insole).
4. `balancetrack run data/s001.csv --height 175 --weight 70 --shoe 10 --system us-men --foot left --both -o out`
5. Open `out/insole_left.stl` in a slicer.

`out/report_left.png` shows the detected heel strikes, how each measurement compares to expected, and the thickness map. `report_left.json` has all the numbers.

Other commands:

```
balancetrack analyze <csv> ...          report + thickness map only
balancetrack build out/insole_left.npz  STL from a saved thickness map
balancetrack simulate --profile medial  fake walk (normal, medial, lateral, unstable, shuffle, hard)
```

Tests: `pytest analysis/tests`

## Printing

0.2 mm layers, 3 walls, 20-30% gyroid infill, no supports needed since the bottom is flat. Print it upside down on a textured plate if you want grip on the bottom. Trim the toe to fit the shoe if needed.

## Notes

The expected values in `analysis/balancetrack/data/reference_norms.json` are rough starting points based on typical adult walking numbers, not clinical norms. They're meant to be edited. This is a student project, not a medical device, and it isn't a replacement for a physiotherapist or a real orthotic.

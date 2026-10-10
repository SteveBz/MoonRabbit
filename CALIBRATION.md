# Calibration

> **You are here:** calibration — validating and adjusting sensor readings.
> Jump to: [README](README.md) · [BOM](BOM.md) · [BUILD](BUILD.md) · [SOFTWARE BUILD](SOFTWARE_BUILD.md)

Procedures for validating and calibrating the Moon Rabbit sensors.

## CO<sub>2</sub> (SCD30)

The SCD30 uses NDIR (non-dispersive infrared) sensing. Out of the box, some units are accurate to within a few ppm, others can be out by 150 ppm or more.

### Reference calibration

The most reliable method is to compare against a known concentration source — for example a calibrated reference gas cylinder, or a nearby reference-grade CO<sub>2</sub> monitor.

### Field calibration

In the absence of a reference source, the following approaches help:

- **Fresh-air baseline**: place the sensor outdoors in clean air, well away from traffic and buildings, for 20–30 minutes. Fresh outdoor air is around 420 ppm. Use the SCD30's built-in `forced_recalibration` command to anchor to this value.
- **Continuous baseline correction**: the SCD30 supports automatic baseline correction (ABC), which assumes the sensor will periodically see fresh air. Enable this only if the sensor is in a space that genuinely drops to outdoor levels regularly — otherwise it will slowly drift.

### Recording the calibration

Update the following fields in `config.json`:

- `last_calibration_date` — ISO timestamp
- `last_calibration_value` — the reference ppm used

## Temperature and humidity

The BME280 and SHT41 do not normally need field calibration. If you have a reference instrument:

- SHT41 is accurate to ±0.1 °C / ±1.7 %RH
- BME280 is accurate to ±0.5 °C / ±3 %RH

If you see a systematic offset, it is more likely due to self-heating from nearby electronics than to a bad sensor. Consider re-siting.

## Pressure

Barometric pressure varies naturally by ±15 hPa over a day due to weather. Do not attempt to calibrate it in isolation — cross-check against a nearby official weather station reading after accounting for altitude difference.

## Other sensors

- **VOC / NOx (SGP41)** — needs a 10-hour burn-in and conditioning cycle before readings stabilise. No user calibration.
- **Lux (TSL2591)** — factory calibrated; no user adjustment.

---

*This document is a work in progress. Contributions welcome.*

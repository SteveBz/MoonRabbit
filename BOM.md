# Bill of Materials

> **You are here:** bill of materials — the parts list.
> Jump to: [README](README.md) · [BUILD](BUILD.md) · [SOFTWARE BUILD](SOFTWARE_BUILD.md) · [CALIBRATION](CALIBRATION.md)

Everything required to build one Moon Rabbit station. Prices are indicative (GBP, 2026), exclude shipping, and assume a UK/EU supplier. Substitute your preferred source.

## Enclosure

| Item | Qty | Notes | Source |
|------|-----|-------|--------|
| 3D-printed base | 1 | [`MoonRabbitCase_v0.4.stl`](MoonRabbitCase_v0.4.stl) | Print locally |
| 3D-printed shell | 1 | [`CarbonSensorStand_v0.9.stl`](CarbonSensorStand_v0.9.stl) | Print locally |
| M2 threaded inserts (shell) | 4 | Heat-set, ~4 mm | Generic |
| M3 threaded inserts (base) | 8 | Heat-set | Generic |
| M2 × 8 mm hex-head bolts | 4 | Attach shell to base | Generic |
| M2.5 × 6 mm cross-head bolts | 8 | Mount Pi and Qwiic HAT | Generic |
| M2.5 × 6 mm standoffs | 8 | Between Pi and Qwiic HAT | Generic |
| M2.5 × 11 mm standoffs | 2 | Sensor mounting | Generic |

## Electronics

| Item | Qty | Notes | Source |
|------|-----|-------|--------|
| Raspberry Pi Zero 2 W **or** WH | 1 | **WH** = pre-soldered GPIO header (recommended) | Pi Hut / Adafruit |
| 40-pin GPIO header | 1 | Only if using the non-WH board | Generic |
| SparkFun Qwiic pHAT for Pi | 1 | I²C breakout + Qwiic socket | SparkFun |
| Bosch BME280 breakout | 1 | Qwiic or pinout version | Adafruit / SparkFun |
| Sensirion SCD30 CO<sub>2</sub> sensor | 1 | NDIR. Qwiic version recommended | Sensirion / SparkFun |
| Qwiic-to-Qwiic cable, 10 cm | 1 | HAT → SCD30 | SparkFun |
| Qwiic-to-4-pin-female cable | 1 | HAT → BME280 (pinout version only) | SparkFun |
| MicroSD card, 32 GB, Class 10 | 1 | Samsung / SanDisk recommended | Generic |
| MicroSD card reader | 1 | For flashing the Pi | Generic |

## Optional upgrades

| Item | Qty | Notes | Source |
|------|-----|-------|--------|
| SHT41 breakout | 1 | Better humidity precision than BME280 | Adafruit / SparkFun |
| SGP41 breakout | 1 | VOC / NOx gas sensing | Sensirion / Adafruit |
| TSL2591 breakout | 1 | Sky luminosity (lux, IR, full spectrum) | Adafruit |
| Qwiic cable, 5 cm | 2–3 | One per upgrade sensor | SparkFun |
| IP65 enclosure, clear window | 1 | For the outdoor TSL2591 | Generic |
| Outdoor mounting bracket | 1 | For the IP65 enclosure | Generic |
| 4-core cable, ~2 m | 1 | TSL2591 (outdoor) → main case | Generic |
| 4-pole 2.5 mm panel socket | 1 | On the main case | Generic |
| 4-pole 2.5 mm plug | 1 | On the outdoor box | Generic |

## Tools

| Item | Notes |
|------|-------|
| Electric screwdriver | e.g. Homtronics 37 in 1 electric screwdriver — speeds assembly |
| Miniware TS101 soldering iron | Heat-set inserts, pin headers |
| Solder, 0.6–0.8 mm lead-free | Fine-pitch work |
| Soldering stand / helping hands | Holds small boards during soldering |
| Silicone soldering mat | Heat-resistant, keeps parts in place |

## Not included

- **Power supply** — the Pi Zero 2 W needs a **5 V, 2.5 A micro-USB** supply (not USB-C).
- **Weather station** — Vantage Pro, Ambient Weather, or Ecowitt, purchased separately. See [SOFTWARE_BUILD.md](SOFTWARE_BUILD.md) for setup.

## Approximate cost

| Tier | Cost (GBP) |
|------|------------|
| Core kit | £70–£90 |
| + SHT41 | +£12 |
| + SGP41 | +£20 |
| + TSL2591 outdoor kit | +£25 |
| + Weather station | £150–£500 (model dependent) |

---

*See [BUILD.md](BUILD.md) for assembly, [SOFTWARE_BUILD.md](SOFTWARE_BUILD.md) for the software setup.*

# Contributing to Moon Rabbit

Thanks for your interest. This document explains how to report problems, propose changes, and work with the existing code and hardware design.

> **You are here:** how to contribute.
> Jump to: [README](README.md) · [BOM](BOM.md) · [BUILD](BUILD.md) · [SOFTWARE BUILD](SOFTWARE_BUILD.md) · [CALIBRATION](CALIBRATION.md)

## Ways to contribute

- **Bug reports** — if something doesn't work, open an issue.
- **Documentation fixes** — typos, unclear steps, missing screenshots. Always welcome.
- **Sensor integrations** — new sensors compatible with the Qwiic / I²C bus.
- **Weather station integrations** — additional station models supported by `ecowitt2mqtt` or `indi2mqtt`.
- **Hardware modifications** — case revisions, mounting brackets, PCB layouts.
- **Translations** — of this document set.

Please **open an issue first** if you're planning anything more than a small fix, so we can agree on the approach before you spend time on it.

## Reporting a bug

Include as much of the following as you can:

- **Moon Rabbit version** — `git rev-parse HEAD` in the repo root
- **Pi model** — Zero 2 W, Zero 2 WH, etc.
- **Sensor list** — which sensors are attached and which are absent
- **Weather source** — `vantage`, `ecowitt`, or `none` (from `config.json`)
- **Relevant log lines** — `sudo supervisorctl tail -200 <program> stderr`
- **What you expected** vs **what you saw**

If the problem is intermittent, note how often it happens and whether it correlates with anything else (weather, time of day, WiFi dropout).

## Submitting a change

1. **Fork** the repository and create a branch:
   ```bash
   git checkout -b fix/descriptive-name
   ```
2. **Make the change.** Keep commits focused — one logical change per commit.
3. **Test.** See "Testing" below.
4. **Push** to your fork and open a Pull Request against `main`.
5. **Describe the change** in the PR — what it fixes, how you tested it, and any side effects.

Small fixes (typos, one-line bugs) can go straight to a PR without a prior issue.

## Code style

- **Python** — follow PEP 8. The existing code uses 4-space indentation, no tabs.
- **Commit messages** — imperative mood, first line under 72 characters. E.g. `Fix rain_mm aggregation at midnight`, not `fixed stuff`.
- **No reformatting PRs** — if you want to change whitespace or style across a file, open an issue first.

## Testing

The easiest way to test a change is to run it on a spare Pi with the relevant sensors. If you don't have one:

- **Software changes** can often be tested in isolation — e.g. the aggregation logic in `class_config_mgt.py` can be exercised with a small Python script.
- **Weather integrations** require a real station or a replay of captured MQTT traffic.
- **Hardware changes** should include a printed photo of the result.

Mention in the PR how you tested, and what you couldn't test.

## Hardware contributions

- **Case / bracket changes** — submit the source file (Fusion 360, OpenSCAD, FreeCAD) alongside the exported STL.
- **PCB changes** — KiCad project directory, not just Gerbers.
- **Wiring changes** — a photo or a schematic, plus an update to `BOM.md` and `BUILD.md`.

## Licensing

By contributing, you agree that:

- **Software contributions** are licensed under the project's MIT licence.
- **Hardware contributions** are licensed under CC BY-SA 4.0.

You retain copyright to your contribution. Add a `Signed-off-by: Your Name <email>` line to each commit (the standard DCO sign-off):

```bash
git commit -s -m "Fix rain_mm aggregation at midnight"
```

## Questions

If anything is unclear, open an issue and ask. It's better to ask than to guess.

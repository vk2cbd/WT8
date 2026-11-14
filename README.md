# WT8 — Two-antenna radio astronomy controller

WT8 is the PyQt5 successor to WT7 v0.31 (source commit `1a42515a4f40d6dd43469572b3497d28bbf952c4`).
The original WT7 source is preserved in the preceding WT8 migration-baseline commit `b0cb6328aeff805f6f84d46951dd500026c59c66`.

## Install

```bash
python3 -m pip install -r requirements.txt
```

On Ubuntu, configure serial permissions, UHD/SoapySDR, B210 support and stable /dev/serial/by-id device paths.

## Configure

```bash
cp wt8_ubuntu.ini.example wt8_ubuntu.ini
nano wt8_ubuntu.ini
```

Copying an existing WT7 INI is supported: missing Service coordinates default to AZ 0°, EL 5°. Each `[antenna:East]` and `[antenna:West]` section can define its own `service_az` and `service_el`. They can also be edited in the Limits dialog. Check limits and mechanical clearance before use.

## Run

```bash
python3 wt8_ubuntu_gui.py --config wt8_ubuntu.ini
```

## Service function (WT8 v0.2)

The **Service** button is between **Stop Track** and **Park**. It stops source tracking and drives each connected antenna to its fixed configured service coordinates. It does not track after arrival or disconnect. It uses the existing `SafeAntenna.guarded_slew_to` motion protection and performs a separate preflight that rejects any Service target outside the permitted AZ/EL arc or inside the configured safety margins plus stopping tolerances. If either connected antenna fails preflight, neither begins a Service move.

**STOP ALL** requests cancellation of Service and sends the existing antenna stop commands. Other drive workflows are blocked while Service is active. No software check substitutes for physical clearance or hardware end stops; the initial 0° AZ / 5° EL must be verified safe for both antennas before live use.

## Precision Park and Service (verification update)

Both fixed-position commands now use `wt8_precision.precision_fixed_slew`.
The routine disables direction-dependent azimuth target compensation **only for Park and Service**; tracking retains its existing behaviour. It commands a guarded slew, waits 1 second for settling, reads fresh encoders and checks the *requested* coordinates within ±0.15° on both axes. If necessary it makes at most two additional guarded low-speed corrections, verifying after each. Failure to meet tolerance raises a positioning fault instead of displaying PARKED/SERVICE. The preflight rejects targets near configured limits (margin plus 0.15°); this may reject previously accepted Park coordinates. All motion still uses the established safety controller.

The event log records `PARK_VERIFY` and `SERVICE_VERIFY` with attempt, target, measured coordinates and error. Cancellation is supported by STOP ALL or individual antenna STOP; cancelled operations do not report success. **This has not yet been validated on actual antenna hardware.** Do not use these moves for unattended or personnel-safe maintenance until mechanical clearances, approach directions and stopping distances have been tested.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Hardware tests are required before operational use. The software tests do not establish physical safety.

## Repository contents

- `wt8_ubuntu_gui.py`: PyQt5 GUI and Service workflow
- `wt8_antenna.py`: Arduino protocol and guarded motion
- `wt8_service.py`: fixed Service destination preflight
- `wt8_config.py`: INI configuration
- `wt8_b210_power.py`: B210 power measurement
- `wt8_tk_legacy_gui.py`: historical Tkinter GUI reference
- `tests/`: automated regression tests
- `WT7_*.md`: archived WT7 documentation, intentionally retained under original titles

The original WT7 application-description PDF remains in WT7. The GitHub connector could not transfer that binary file to WT8; refer to the WT7 repository for it.

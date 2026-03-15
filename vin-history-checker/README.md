# VIN History Checker

A zero-dependency Python 3 command-line tool that:

1. **Validates** a 17-character VIN (length, forbidden characters, check digit)
2. **Decodes** every section — WMI, VDS, VIS, country of origin, model year, plant code, serial number
3. **Generates direct links** to six public vehicle-history and recall databases

## Requirements

Python 3.9 or later. No third-party packages needed.

## Usage

```
python3 vin_checker.py <VIN>
```

### Example

```
$ python3 vin_checker.py 3MZBM1U77FM131942

VIN History Checker — 3MZBM1U77FM131942

────────────────────────────────────────────────────────────
  Validation
────────────────────────────────────────────────────────────
  ✓ VIN structure and check digit are valid.

────────────────────────────────────────────────────────────
  Decoded Fields
────────────────────────────────────────────────────────────
  Full VIN           3MZBM1U77FM131942
  WMI (pos 1–3)      3MZ
  VDS (pos 4–9)      BM1U77
  VIS (pos 10–17)    FM131942
  Country of origin  Mexico
  Model year code    F
  Possible year(s)   1985 or 2015
  Assembly plant     M
  Serial number      131942
  Check digit        7  ✓  (weighted sum 381 mod 11 = 7)

────────────────────────────────────────────────────────────
  Vehicle History Lookup Links
────────────────────────────────────────────────────────────
  NHTSA (US Government — free)
    https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/3MZBM1U77FM131942?format=json
    Official US NHTSA VIN decoder; returns make, model, year, body type, and more.

  NHTSA Safety Recalls
    https://api.nhtsa.gov/recalls/recallsByVehicle?vin=3MZBM1U77FM131942
    Check for open safety recalls on the vehicle.

  VehicleHistory.com
    https://www.vehiclehistory.com/vin-check/3MZBM1U77FM131942
    Free summary report: title, ownership, accident history.

  AutoCheck (Experian)
    https://www.autocheck.com/vehiclehistory/autocheck/en/vinbasic?vin=3MZBM1U77FM131942
    Paid full vehicle history report from Experian.

  Carfax
    https://www.carfax.com/VehicleHistory/p/Report.cfx?partner=DVW_1&vin=3MZBM1U77FM131942
    Paid full vehicle history report (accidents, service, ownership).

  iSeeCars
    https://www.iseecars.com/vin#3MZBM1U77FM131942
    Free VIN decoder with market value and listing search.
```

### Invalid VIN example

```
$ python3 vin_checker.py 3MZBM1U77FM13194X

VIN History Checker — 3MZBM1U77FM13194X

────────────────────────────────────────────────────────────
  Validation
────────────────────────────────────────────────────────────
  ✗ INVALID VIN
    • Check digit mismatch: position 9 is '7', calculated value is '6' ...
```

The tool exits with code `0` for a valid VIN and `1` for an invalid one.

## Running the tests

```
python3 test_vin_checker.py
```

24 tests covering validation, decoding, and link generation.

## API

The tool is also importable as a module:

```python
from vin_checker import validate_vin, decode_vin, history_links

errors = validate_vin("3MZBM1U77FM131942")   # [] means valid
fields = decode_vin("3MZBM1U77FM131942")      # dict of decoded sections
links  = history_links("3MZBM1U77FM131942")   # list of service dicts
```

## Related documentation

- [VIN.md](../VIN.md) — VIN structure reference with a fully annotated example

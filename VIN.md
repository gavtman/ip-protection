# VIN samochodu (Vehicle Identification Number)

A **Vehicle Identification Number (VIN)** is a unique 17-character alphanumeric code assigned to every motor vehicle when it is manufactured. It serves as the vehicle's fingerprint — no two vehicles in operation have the same VIN.

## Structure

A standard VIN is composed of three sections:

| Section | Characters | Description |
|---------|-----------|-------------|
| World Manufacturer Identifier (WMI) | 1–3 | Identifies the country of manufacture and the manufacturer |
| Vehicle Descriptor Section (VDS) | 4–9 | Describes the vehicle's model, body type, engine type, and check digit |
| Vehicle Identifier Section (VIS) | 10–17 | Uniquely identifies the individual vehicle (model year, plant, serial number) |

### Example

```
3MZBM1U77FM131942
│││└────┘│└──────┘
│││  VDS ││  VIS
│││      │└─ Sequential number (131942)
│││      └── Model year F = 2015, Plant M
││└ Check digit (position 9) = 7  ✓
│└─ MZ = Mazda Motor Manufacturing de Mexico
└── 3 = Mexico
```

Decoded:

| Field | Value | Meaning |
|-------|-------|---------|
| WMI | `3MZ` | Mazda Motor Manufacturing de Mexico |
| VDS | `BM1U7` | Model/body/engine descriptor |
| Check digit | `7` | Mathematically valid (sum 381 mod 11 = 7) |
| Model year | `F` | 2015 |
| Plant | `M` | Assembly plant code |
| Sequence | `131942` | Sequential production number |

## Where to Find the VIN

- **Dashboard** — visible through the windshield on the driver's side
- **Driver's door jamb** — on a sticker or plate inside the door frame
- **Vehicle title and registration** documents
- **Insurance card**
- **Engine block** — stamped directly on the engine

## Privacy Considerations

Like an IP address, a VIN is a unique identifier that can be used to track a vehicle and, by extension, its owner. Information associated with a VIN may include:

- Ownership history
- Service and accident records
- Geographic location data from toll systems, parking, and service records
- Theft or recall status

Databases such as manufacturer portals, insurance records, and third-party vehicle history services aggregate data against VINs in ways that are often opaque to vehicle owners.

## VIN Check Digit (Position 9)

The ninth character is a mathematical check digit computed from the other 16 characters using a defined weighting formula. It allows basic detection of transcription errors or fraudulent VINs.

**Transliteration table (letters → digits):**

| A=1 | B=2 | C=3 | D=4 | E=5 | F=6 | G=7 | H=8 |
|-----|-----|-----|-----|-----|-----|-----|-----|
| J=1 | K=2 | L=3 | M=4 | N=5 | — | P=7 | R=9 |
| S=2 | T=3 | U=4 | V=5 | W=6 | X=7 | Y=8 | Z=9 |

**Position weights (positions 1–17, check digit at position 9 has weight 0):**

| Pos | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 |
|-----|---|---|---|---|---|---|---|---|---|----|----|----|----|----|----|----|----|
| Wt  | 8 | 7 | 6 | 5 | 4 | 3 | 2 |10 | 0 |  9 |  8 |  7 |  6 |  5 |  4 |  3 |  2 |

The weighted sum is divided by 11; the remainder gives the check digit (remainder 10 → `X`).

## Standards

- **ISO 3779** — defines the VIN structure internationally
- **ISO 3780** — defines the World Manufacturer Identifier (WMI) codes
- **FMVSS 115** — US federal standard requiring VIN on all road vehicles since 1981

## VIN History Checker Tool

The [`vin-history-checker/`](vin-history-checker/) directory contains a zero-dependency Python 3
command-line tool that validates any VIN, decodes all of its fields, and generates
direct links to public vehicle-history databases (NHTSA, Carfax, AutoCheck, and others).

```
python3 vin-history-checker/vin_checker.py 3MZBM1U77FM131942
```

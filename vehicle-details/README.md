# Vehicle Details Manager

A zero-dependency Python 3 command-line tool for storing and updating
user-supplied details for vehicles identified by their
[VIN](../VIN.md).

Details are persisted locally in a `vehicles.json` file in this directory.

---

## Requirements

- Python 3.10 or later (uses built-in `json`, `os`, `sys`, `datetime`)
- No third-party packages required

---

## Usage

```
python3 vehicle_details.py add    <VIN>
python3 vehicle_details.py update <VIN> <field> <value>
python3 vehicle_details.py show   <VIN>
python3 vehicle_details.py list
python3 vehicle_details.py remove <VIN>
```

### Commands

| Command            | Description                                              |
|--------------------|----------------------------------------------------------|
| `add <VIN>`        | Validate the VIN, decode static fields, create a record  |
| `update <VIN> <field> <value>` | Set a user-editable field on an existing record |
| `show <VIN>`       | Display all details for a vehicle                        |
| `list`             | List all tracked vehicles with owner and nickname        |
| `remove <VIN>`     | Delete a vehicle record from the store                   |

### Updatable fields

| Field           | Type   | Description                          |
|-----------------|--------|--------------------------------------|
| `owner`         | string | Name of the current owner            |
| `purchase_date` | string | Date the vehicle was purchased        |
| `mileage`       | int    | Current odometer reading (integer)   |
| `color`         | string | Exterior colour                      |
| `license_plate` | string | Registration / licence-plate number  |
| `nickname`      | string | Friendly name for the vehicle        |
| `notes`         | string | Free-form notes                      |

---

## Example session

```
$ python3 vehicle_details.py add 3MZBM1U77FM131942

✓ Added 3MZBM1U77FM131942.

────────────────────────────────────────────────────────────
  Vehicle — 3MZBM1U77FM131942
────────────────────────────────────────────────────────────

  — Decoded (from VIN) —
  WMI (pos 1–3)       3MZ
  Country of origin   Mexico
  Possible year(s)    1985 or 2015
  Assembly plant      M
  Serial number       131942

  — User details —
  Owner               —
  Nickname            —
  Color               —
  License plate       —
  Purchase date       —
  Mileage             —
  Notes               —

  — Metadata —
  Added               2026-03-15T04:05:00Z
  Last updated        2026-03-15T04:05:00Z
```

```
$ python3 vehicle_details.py update 3MZBM1U77FM131942 owner "Jane Smith"
✓ Updated 3MZBM1U77FM131942 — owner = 'Jane Smith'

$ python3 vehicle_details.py update 3MZBM1U77FM131942 mileage 45230
✓ Updated 3MZBM1U77FM131942 — mileage = 45230

$ python3 vehicle_details.py update 3MZBM1U77FM131942 color "Soul Red Crystal"
✓ Updated 3MZBM1U77FM131942 — color = 'Soul Red Crystal'

$ python3 vehicle_details.py update 3MZBM1U77FM131942 nickname "Zoom-Zoom"
✓ Updated 3MZBM1U77FM131942 — nickname = 'Zoom-Zoom'
```

```
$ python3 vehicle_details.py show 3MZBM1U77FM131942

────────────────────────────────────────────────────────────
  Vehicle — 3MZBM1U77FM131942
────────────────────────────────────────────────────────────

  — Decoded (from VIN) —
  WMI (pos 1–3)       3MZ
  Country of origin   Mexico
  Possible year(s)    1985 or 2015
  Assembly plant      M
  Serial number       131942

  — User details —
  Owner               Jane Smith
  Nickname            Zoom-Zoom
  Color               Soul Red Crystal
  License plate       —
  Purchase date       —
  Mileage             45230
  Notes               —

  — Metadata —
  Added               2026-03-15T04:05:00Z
  Last updated        2026-03-15T04:06:30Z
```

```
$ python3 vehicle_details.py list

────────────────────────────────────────────────────────────
  Tracked Vehicles
────────────────────────────────────────────────────────────
  VIN                 Nickname            Owner
  ─────────────────   ───────────────     ────────────────────
  3MZBM1U77FM131942   Zoom-Zoom           Jane Smith
```

---

## Importable API

The module can be imported and used programmatically:

```python
from vehicle_details import add_vehicle, update_vehicle, get_vehicle, list_vehicles, remove_vehicle

store = "/path/to/my-vehicles.json"

add_vehicle("3MZBM1U77FM131942", store)
update_vehicle("3MZBM1U77FM131942", "owner", "Jane Smith", store)
record = get_vehicle("3MZBM1U77FM131942", store)
print(record["owner"])  # Jane Smith

all_vehicles = list_vehicles(store)
remove_vehicle("3MZBM1U77FM131942", store)
```

---

## Running the tests

```
python3 -m pytest test_vehicle_details.py -v
```

or without pytest:

```
python3 test_vehicle_details.py
```

#!/usr/bin/env python3
"""
Vehicle Details Manager
=======================
Stores and updates user-supplied details for vehicles identified by VIN.
Details are persisted in a JSON file (``vehicles.json`` by default).

Usage:
    python3 vehicle_details.py add    <VIN>
    python3 vehicle_details.py update <VIN> <field> <value>
    python3 vehicle_details.py show   <VIN>
    python3 vehicle_details.py list
    python3 vehicle_details.py remove <VIN>

Example:
    python3 vehicle_details.py add    3MZBM1U77FM131942
    python3 vehicle_details.py update 3MZBM1U77FM131942 owner "Jane Smith"
    python3 vehicle_details.py update 3MZBM1U77FM131942 mileage 45230
    python3 vehicle_details.py show   3MZBM1U77FM131942
"""

import json
import os
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_STORE = os.path.join(os.path.dirname(__file__), "vehicles.json")

# Fields that users are allowed to set or update.
UPDATABLE_FIELDS: tuple[str, ...] = (
    "owner",
    "purchase_date",
    "mileage",
    "color",
    "license_plate",
    "nickname",
    "notes",
)

# ---------------------------------------------------------------------------
# VIN validation (minimal — mirrors the logic in vin-history-checker)
# ---------------------------------------------------------------------------

_TRANSLITERATION: dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5,           "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
}

_WEIGHTS: list[int] = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]

_MODEL_YEAR: dict[str, list[int]] = {
    "A": [1980, 2010], "B": [1981, 2011], "C": [1982, 2012], "D": [1983, 2013],
    "E": [1984, 2014], "F": [1985, 2015], "G": [1986, 2016], "H": [1987, 2017],
    "J": [1988, 2018], "K": [1989, 2019], "L": [1990, 2020], "M": [1991, 2021],
    "N": [1992, 2022], "P": [1993, 2023], "R": [1994, 2024], "S": [1995, 2025],
    "T": [1996, 2026], "V": [1997, 2027], "W": [1998, 2028], "X": [1999, 2029],
    "Y": [2000, 2030], "1": [2001, 2031], "2": [2002, 2032], "3": [2003, 2033],
    "4": [2004, 2034], "5": [2005, 2035], "6": [2006, 2036], "7": [2007, 2037],
    "8": [2008, 2038], "9": [2009, 2039],
}

_COUNTRY: dict[str, str] = {
    "1": "United States", "2": "Canada", "3": "Mexico",
    "4": "United States", "5": "United States",
    "6": "Australia", "7": "New Zealand",
    "8": "Argentina", "9": "Brazil",
    "A": "South Africa", "B": "Angola / Kenya / Tanzania",
    "C": "Benin / Madagascar / Mauritius",
    "D": "Egypt / Morocco",
    "E": "Ethiopia / Mozambique",
    "F": "Ghana / Nigeria",
    "G": "Cameroon / Ivory Coast",
    "H": "Libya / Senegal / Tunisia",
    "J": "Japan", "K": "South Korea",
    "L": "China", "M": "India",
    "N": "Indonesia / Turkey",
    "P": "Philippines",
    "R": "Taiwan",
    "S": "United Kingdom",
    "T": "Switzerland / Czech Republic / Hungary",
    "U": "Denmark / Poland / Romania",
    "V": "Austria / France / Spain",
    "W": "Germany",
    "X": "Russia / Belarus / Kazakhstan",
    "Y": "Belgium / Finland / Sweden",
    "Z": "Italy / Slovenia",
}


def _char_value(c: str) -> int:
    if c.isdigit():
        return int(c)
    return _TRANSLITERATION.get(c, -1)


def validate_vin(vin: str) -> list[str]:
    """Return a list of validation error strings; empty list means valid."""
    vin = vin.strip().upper()
    errors: list[str] = []

    if len(vin) != 17:
        errors.append(f"Length is {len(vin)}, must be 17 characters.")

    forbidden = set(vin) & {"I", "O", "Q"}
    if forbidden:
        errors.append(f"Contains forbidden character(s): {', '.join(sorted(forbidden))}.")

    invalid_chars = {c for c in vin if not c.isalnum()}
    if invalid_chars:
        errors.append(f"Contains non-alphanumeric character(s): {', '.join(sorted(invalid_chars))}.")

    if errors:
        return errors

    total = sum(_char_value(c) * w for c, w in zip(vin, _WEIGHTS))
    remainder = total % 11
    expected = "X" if remainder == 10 else str(remainder)
    if vin[8] != expected:
        errors.append(
            f"Check digit mismatch: position 9 is '{vin[8]}', "
            f"calculated value is '{expected}' (weighted sum {total}, mod 11 = {remainder})."
        )

    return errors


def _decode_static_fields(vin: str) -> dict:
    """Decode the fixed, VIN-derived fields (country, possible years, etc.)."""
    vin = vin.upper()
    years = _MODEL_YEAR.get(vin[9], [])
    return {
        "wmi": vin[0:3],
        "country_of_origin": _COUNTRY.get(vin[0], "Unknown"),
        "possible_years": years,
        "assembly_plant": vin[10],
        "serial_number": vin[11:17],
    }


# ---------------------------------------------------------------------------
# Store operations
# ---------------------------------------------------------------------------

def load_store(path: str = DEFAULT_STORE) -> dict:
    """Load the JSON store; return an empty dict if the file does not exist."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_store(store: dict, path: str = DEFAULT_STORE) -> None:
    """Persist the store to disk, creating the file if necessary."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(store, fh, indent=2)
        fh.write("\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_vehicle(vin: str, store_path: str = DEFAULT_STORE) -> dict:
    """
    Validate *vin*, create a new record with decoded static fields, and
    persist it to *store_path*.

    Returns the new record dict, or raises ``ValueError`` on invalid VIN or
    if the VIN is already present.
    """
    vin = vin.strip().upper()
    errors = validate_vin(vin)
    if errors:
        raise ValueError("Invalid VIN:\n" + "\n".join(f"  • {e}" for e in errors))

    store = load_store(store_path)
    if vin in store:
        raise ValueError(f"Vehicle {vin} is already in the store.")

    record: dict = {
        "vin": vin,
        **_decode_static_fields(vin),
        # User-updatable fields start empty / null
        "owner": None,
        "purchase_date": None,
        "mileage": None,
        "color": None,
        "license_plate": None,
        "nickname": None,
        "notes": None,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }

    store[vin] = record
    save_store(store, store_path)
    return record


def update_vehicle(
    vin: str,
    field: str,
    value: str,
    store_path: str = DEFAULT_STORE,
) -> dict:
    """
    Update a single user-editable *field* for the vehicle identified by *vin*.

    Returns the updated record, or raises ``KeyError`` / ``ValueError`` on
    unknown VIN or unsupported field.
    """
    vin = vin.strip().upper()
    if field not in UPDATABLE_FIELDS:
        raise ValueError(
            f"'{field}' is not an updatable field.\n"
            f"Updatable fields: {', '.join(UPDATABLE_FIELDS)}"
        )

    store = load_store(store_path)
    if vin not in store:
        raise KeyError(f"Vehicle {vin} not found. Use 'add' first.")

    record = store[vin]

    # Coerce mileage to int when possible
    if field == "mileage":
        try:
            record[field] = int(value)
        except ValueError:
            raise ValueError(f"'mileage' must be an integer; got '{value}'.")
    else:
        record[field] = value

    record["updated_at"] = _now_iso()
    store[vin] = record
    save_store(store, store_path)
    return record


def get_vehicle(vin: str, store_path: str = DEFAULT_STORE) -> dict:
    """
    Return the record for *vin*, raising ``KeyError`` if it is not found.
    """
    vin = vin.strip().upper()
    store = load_store(store_path)
    if vin not in store:
        raise KeyError(f"Vehicle {vin} not found.")
    return store[vin]


def list_vehicles(store_path: str = DEFAULT_STORE) -> list[dict]:
    """Return all vehicle records sorted by VIN."""
    store = load_store(store_path)
    return sorted(store.values(), key=lambda r: r["vin"])


def remove_vehicle(vin: str, store_path: str = DEFAULT_STORE) -> dict:
    """
    Remove the record for *vin* from the store.

    Returns the removed record, or raises ``KeyError`` if not found.
    """
    vin = vin.strip().upper()
    store = load_store(store_path)
    if vin not in store:
        raise KeyError(f"Vehicle {vin} not found.")
    record = store.pop(vin)
    save_store(store, store_path)
    return record


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _header(text: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {text}")
    print(f"{'─' * 60}")


def _print_record(record: dict) -> None:
    _header(f"Vehicle — {record['vin']}")

    static_labels = [
        ("WMI (pos 1–3)",     record.get("wmi", "")),
        ("Country of origin", record.get("country_of_origin", "")),
        (
            "Possible year(s)",
            " or ".join(str(y) for y in record.get("possible_years", [])) or "Unknown",
        ),
        ("Assembly plant",    record.get("assembly_plant", "")),
        ("Serial number",     record.get("serial_number", "")),
    ]

    user_labels = [
        ("Owner",         record.get("owner") or "—"),
        ("Nickname",      record.get("nickname") or "—"),
        ("Color",         record.get("color") or "—"),
        ("License plate", record.get("license_plate") or "—"),
        ("Purchase date", record.get("purchase_date") or "—"),
        ("Mileage",       str(record.get("mileage")) if record.get("mileage") is not None else "—"),
        ("Notes",         record.get("notes") or "—"),
    ]

    meta_labels = [
        ("Added",         record.get("created_at", "")),
        ("Last updated",  record.get("updated_at", "")),
    ]

    all_labels = static_labels + user_labels + meta_labels
    col = max(len(lbl) for lbl, _ in all_labels) + 2

    print("\n  — Decoded (from VIN) —")
    for label, value in static_labels:
        print(f"  {label:<{col}}{value}")

    print("\n  — User details —")
    for label, value in user_labels:
        print(f"  {label:<{col}}{value}")

    print("\n  — Metadata —")
    for label, value in meta_labels:
        print(f"  {label:<{col}}{value}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _usage() -> None:
    prog = os.path.basename(sys.argv[0])
    print(
        f"\nUsage:\n"
        f"  python3 {prog} add    <VIN>\n"
        f"  python3 {prog} update <VIN> <field> <value>\n"
        f"  python3 {prog} show   <VIN>\n"
        f"  python3 {prog} list\n"
        f"  python3 {prog} remove <VIN>\n"
        f"\nUpdatable fields: {', '.join(UPDATABLE_FIELDS)}\n"
        f"\nExample:\n"
        f"  python3 {prog} add    3MZBM1U77FM131942\n"
        f"  python3 {prog} update 3MZBM1U77FM131942 owner \"Jane Smith\"\n"
        f"  python3 {prog} show   3MZBM1U77FM131942\n"
    )


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    if not args:
        _usage()
        return 1

    cmd = args[0].lower()

    try:
        if cmd == "add":
            if len(args) != 2:
                print("Usage: add <VIN>")
                return 1
            record = add_vehicle(args[1])
            print(f"✓ Added {record['vin']}.")
            _print_record(record)

        elif cmd == "update":
            if len(args) < 4:
                print("Usage: update <VIN> <field> <value>")
                return 1
            vin, field, value = args[1], args[2], " ".join(args[3:])
            record = update_vehicle(vin, field, value)
            print(f"✓ Updated {record['vin']} — {field} = {record[field]!r}")

        elif cmd == "show":
            if len(args) != 2:
                print("Usage: show <VIN>")
                return 1
            record = get_vehicle(args[1])
            _print_record(record)

        elif cmd == "list":
            vehicles = list_vehicles()
            if not vehicles:
                print("No vehicles in the store.")
                return 0
            _header("Tracked Vehicles")
            col_vin = 20
            col_nick = 20
            print(f"  {'VIN':<{col_vin}}{'Nickname':<{col_nick}}Owner")
            print(f"  {'─' * 17:<{col_vin}}{'─' * 15:<{col_nick}}{'─' * 20}")
            for r in vehicles:
                print(
                    f"  {r['vin']:<{col_vin}}"
                    f"{(r.get('nickname') or ''):<{col_nick}}"
                    f"{r.get('owner') or ''}"
                )

        elif cmd == "remove":
            if len(args) != 2:
                print("Usage: remove <VIN>")
                return 1
            record = remove_vehicle(args[1])
            print(f"✓ Removed {record['vin']}.")

        else:
            print(f"Unknown command: '{cmd}'")
            _usage()
            return 1

    except (ValueError, KeyError) as exc:
        print(f"✗ Error: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

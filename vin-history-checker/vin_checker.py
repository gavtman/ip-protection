#!/usr/bin/env python3
"""
VIN History Checker
===================
Validates a 17-character Vehicle Identification Number (VIN), decodes its
sections, and prints direct links to public vehicle-history databases.

Usage:
    python3 vin_checker.py <VIN>
    python3 vin_checker.py 3MZBM1U77FM131942
"""

import sys
import urllib.parse

# ---------------------------------------------------------------------------
# Data tables
# ---------------------------------------------------------------------------

# ISO 3780 / SAE J853 transliteration: letter → numeric value
_TRANSLITERATION: dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5,           "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
}

# Position weights (1-indexed, position 9 = check digit → weight 0)
_WEIGHTS: list[int] = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]

# Model-year encoding (position 10)
# The sequence repeats: 1980-2009 uses A-9, 2010-2039 reuses the same set.
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

# Country codes (first character of VIN)
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

# Public VIN history / lookup services
_HISTORY_SERVICES: list[dict[str, str]] = [
    {
        "name": "NHTSA (US Government — free)",
        "url_template": "https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json",
        "info": "Official US NHTSA VIN decoder; returns make, model, year, body type, and more.",
    },
    {
        "name": "NHTSA Safety Recalls",
        "url_template": "https://api.nhtsa.gov/recalls/recallsByVehicle?vin={vin}",
        "info": "Check for open safety recalls on the vehicle.",
    },
    {
        "name": "VehicleHistory.com",
        "url_template": "https://www.vehiclehistory.com/vin-check/{vin}",
        "info": "Free summary report: title, ownership, accident history.",
    },
    {
        "name": "AutoCheck (Experian)",
        "url_template": "https://www.autocheck.com/vehiclehistory/autocheck/en/vinbasic?vin={vin}",
        "info": "Paid full vehicle history report from Experian.",
    },
    {
        "name": "Carfax",
        "url_template": "https://www.carfax.com/VehicleHistory/p/Report.cfx?partner=DVW_1&vin={vin}",
        "info": "Paid full vehicle history report (accidents, service, ownership).",
    },
    {
        "name": "iSeeCars",
        "url_template": "https://www.iseecars.com/vin#{vin}",
        "info": "Free VIN decoder with market value and listing search.",
    },
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _char_value(c: str) -> int:
    """Return the numeric value of a VIN character."""
    if c.isdigit():
        return int(c)
    return _TRANSLITERATION.get(c, -1)


def validate_vin(vin: str) -> list[str]:
    """
    Return a list of validation error strings.
    An empty list means the VIN is valid.
    """
    vin = vin.strip().upper()
    errors: list[str] = []

    if len(vin) != 17:
        errors.append(f"Length is {len(vin)}, must be 17 characters.")

    # Forbidden characters: I, O, Q (visually ambiguous)
    forbidden = set(vin) & {"I", "O", "Q"}
    if forbidden:
        errors.append(f"Contains forbidden character(s): {', '.join(sorted(forbidden))}.")

    # Characters must be alphanumeric (after removing forbidden)
    invalid_chars = {c for c in vin if not c.isalnum()}
    if invalid_chars:
        errors.append(f"Contains non-alphanumeric character(s): {', '.join(sorted(invalid_chars))}.")

    if errors:
        # Don't attempt check-digit validation on a malformed VIN
        return errors

    # Check digit (position 9, index 8)
    total = sum(_char_value(c) * w for c, w in zip(vin, _WEIGHTS))
    remainder = total % 11
    expected = "X" if remainder == 10 else str(remainder)
    if vin[8] != expected:
        errors.append(
            f"Check digit mismatch: position 9 is '{vin[8]}', "
            f"calculated value is '{expected}' (weighted sum {total}, mod 11 = {remainder})."
        )

    return errors


def decode_vin(vin: str) -> dict:
    """Decode the major fields of a VIN into a dictionary."""
    vin = vin.upper()
    wmi = vin[0:3]
    vds = vin[3:9]
    vis = vin[9:17]

    country_code = vin[0]
    country = _COUNTRY.get(country_code, "Unknown")

    model_year_char = vin[9]
    possible_years = _MODEL_YEAR.get(model_year_char, [])

    plant = vin[10]
    sequence = vin[11:17]

    check_char = vin[8]
    total = sum(_char_value(c) * w for c, w in zip(vin, _WEIGHTS))
    remainder = total % 11
    expected = "X" if remainder == 10 else str(remainder)
    check_valid = check_char == expected

    return {
        "vin": vin,
        "wmi": wmi,
        "vds": vds,
        "vis": vis,
        "country": country,
        "model_year_char": model_year_char,
        "possible_years": possible_years,
        "plant": plant,
        "sequence": sequence,
        "check_digit": check_char,
        "check_expected": expected,
        "check_valid": check_valid,
        "weighted_sum": total,
    }


def history_links(vin: str) -> list[dict[str, str]]:
    """Return a list of populated history-service entries for the given VIN."""
    result = []
    for svc in _HISTORY_SERVICES:
        entry = dict(svc)
        entry["url"] = svc["url_template"].format(vin=urllib.parse.quote(vin, safe=""))
        result.append(entry)
    return result


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _header(text: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {text}")
    print(f"{'─' * 60}")


def print_report(vin: str) -> int:
    """Print a full report and return 0 (ok) or 1 (invalid VIN)."""
    vin = vin.strip().upper()
    print(f"\nVIN History Checker — {vin}")

    # ── Validation ──────────────────────────────────────────────────────────
    _header("Validation")
    errors = validate_vin(vin)
    if errors:
        print("  ✗ INVALID VIN")
        for e in errors:
            print(f"    • {e}")
        return 1
    print("  ✓ VIN structure and check digit are valid.")

    # ── Decode ───────────────────────────────────────────────────────────────
    decoded = decode_vin(vin)
    _header("Decoded Fields")
    fields = [
        ("Full VIN",          decoded["vin"]),
        ("WMI (pos 1–3)",     decoded["wmi"]),
        ("VDS (pos 4–9)",     decoded["vds"]),
        ("VIS (pos 10–17)",   decoded["vis"]),
        ("Country of origin", decoded["country"]),
        ("Model year code",   decoded["model_year_char"]),
        ("Possible year(s)",  " or ".join(str(y) for y in decoded["possible_years"]) or "Unknown"),
        ("Assembly plant",    decoded["plant"]),
        ("Serial number",     decoded["sequence"]),
        ("Check digit",       f"{decoded['check_digit']}  ✓  (weighted sum {decoded['weighted_sum']} mod 11 = {decoded['weighted_sum'] % 11})"),
    ]
    col = max(len(f[0]) for f in fields) + 2
    for label, value in fields:
        print(f"  {label:<{col}}{value}")

    # ── History lookup links ─────────────────────────────────────────────────
    _header("Vehicle History Lookup Links")
    for svc in history_links(vin):
        print(f"  {svc['name']}")
        print(f"    {svc['url']}")
        print(f"    {svc['info']}")
        print()

    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <VIN>")
        print(f"Example: python3 {sys.argv[0]} 3MZBM1U77FM131942")
        sys.exit(1)

    sys.exit(print_report(sys.argv[1]))


if __name__ == "__main__":
    main()

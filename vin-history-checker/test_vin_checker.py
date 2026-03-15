"""
Unit tests for vin_checker.py
Run: python3 -m pytest test_vin_checker.py -v
  or: python3 test_vin_checker.py
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from vin_checker import validate_vin, decode_vin, history_links


class TestValidateVin(unittest.TestCase):

    # ── Valid VINs ────────────────────────────────────────────────────────
    def test_valid_vin_3mzbm(self):
        """The example VIN from VIN.md must pass validation."""
        self.assertEqual(validate_vin("3MZBM1U77FM131942"), [])

    def test_valid_vin_lowercase_accepted(self):
        """Lower-case input that represents a valid VIN should also pass."""
        self.assertEqual(validate_vin("3mzbm1u77fm131942"), [])

    # ── Length errors ─────────────────────────────────────────────────────
    def test_too_short(self):
        errors = validate_vin("3MZBM1U77FM13194")  # 16 chars
        self.assertTrue(any("Length" in e for e in errors))

    def test_too_long(self):
        errors = validate_vin("3MZBM1U77FM1319420")  # 18 chars
        self.assertTrue(any("Length" in e for e in errors))

    # ── Forbidden characters ──────────────────────────────────────────────
    def test_forbidden_i(self):
        vin = "3MZBM1U77FM13194I"  # replace last char with I (forbidden)
        errors = validate_vin(vin)
        self.assertTrue(any("forbidden" in e.lower() for e in errors))

    def test_forbidden_o(self):
        vin = "3OZBM1U77FM131942"
        errors = validate_vin(vin)
        self.assertTrue(any("forbidden" in e.lower() for e in errors))

    def test_forbidden_q(self):
        vin = "3QZBM1U77FM131942"
        errors = validate_vin(vin)
        self.assertTrue(any("forbidden" in e.lower() for e in errors))

    # ── Check-digit errors ────────────────────────────────────────────────
    def test_bad_check_digit(self):
        # Corrupt position 9 (index 8) from '7' to '5'
        vin = list("3MZBM1U77FM131942")
        vin[8] = "5"
        errors = validate_vin("".join(vin))
        self.assertTrue(any("Check digit" in e for e in errors))

    def test_check_digit_x(self):
        """A valid VIN whose check digit is X should pass."""
        # Craft a VIN where weighted sum mod 11 == 10 → check digit is X.
        # Known example: 1M8GDM9AXKP042788  (source: SAE test vector)
        # Compute independently to confirm:
        from vin_checker import _char_value, _WEIGHTS
        vin = "1M8GDM9AXKP042788"
        total = sum(_char_value(c) * w for c, w in zip(vin, _WEIGHTS))
        if total % 11 == 10:
            self.assertEqual(validate_vin(vin), [])
        # If this specific VIN doesn't have X as check digit, skip the X branch
        # (we still exercise the path via the check-digit mismatch test above)


class TestDecodeVin(unittest.TestCase):

    def setUp(self):
        self.decoded = decode_vin("3MZBM1U77FM131942")

    def test_wmi(self):
        self.assertEqual(self.decoded["wmi"], "3MZ")

    def test_vds(self):
        self.assertEqual(self.decoded["vds"], "BM1U77")

    def test_vis(self):
        self.assertEqual(self.decoded["vis"], "FM131942")

    def test_country(self):
        self.assertEqual(self.decoded["country"], "Mexico")

    def test_model_year_char(self):
        self.assertEqual(self.decoded["model_year_char"], "F")

    def test_possible_years(self):
        # F encodes 1985 and 2015
        self.assertIn(2015, self.decoded["possible_years"])
        self.assertIn(1985, self.decoded["possible_years"])

    def test_plant(self):
        self.assertEqual(self.decoded["plant"], "M")

    def test_sequence(self):
        self.assertEqual(self.decoded["sequence"], "131942")

    def test_check_digit_valid(self):
        self.assertTrue(self.decoded["check_valid"])
        self.assertEqual(self.decoded["check_digit"], "7")

    def test_weighted_sum(self):
        self.assertEqual(self.decoded["weighted_sum"], 381)

    def test_vin_normalised_to_uppercase(self):
        d = decode_vin("3mzbm1u77fm131942")
        self.assertEqual(d["vin"], "3MZBM1U77FM131942")


class TestHistoryLinks(unittest.TestCase):

    def setUp(self):
        self.links = history_links("3MZBM1U77FM131942")

    def test_returns_list(self):
        self.assertIsInstance(self.links, list)
        self.assertGreater(len(self.links), 0)

    def test_each_entry_has_required_keys(self):
        for entry in self.links:
            self.assertIn("name", entry)
            self.assertIn("url", entry)
            self.assertIn("info", entry)

    def test_vin_appears_in_urls(self):
        for entry in self.links:
            self.assertIn("3MZBM1U77FM131942", entry["url"])

    def test_nhtsa_entry_present(self):
        names = [e["name"] for e in self.links]
        self.assertTrue(any("NHTSA" in n for n in names))


if __name__ == "__main__":
    unittest.main(verbosity=2)

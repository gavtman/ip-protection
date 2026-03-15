"""
Unit tests for vehicle_details.py
Run: python3 -m pytest test_vehicle_details.py -v
  or: python3 test_vehicle_details.py
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from vehicle_details import (
    UPDATABLE_FIELDS,
    add_vehicle,
    get_vehicle,
    list_vehicles,
    remove_vehicle,
    update_vehicle,
    validate_vin,
)

EXAMPLE_VIN = "3MZBM1U77FM131942"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmp_store() -> str:
    """Return a path to a fresh temporary JSON store."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.unlink(path)  # let the module create it on first write
    return path


# ---------------------------------------------------------------------------
# VIN validation
# ---------------------------------------------------------------------------

class TestValidateVin(unittest.TestCase):

    def test_valid_example_vin(self):
        self.assertEqual(validate_vin(EXAMPLE_VIN), [])

    def test_valid_lowercase_accepted(self):
        self.assertEqual(validate_vin(EXAMPLE_VIN.lower()), [])

    def test_too_short(self):
        errors = validate_vin(EXAMPLE_VIN[:-1])  # 16 chars
        self.assertTrue(any("Length" in e for e in errors))

    def test_too_long(self):
        errors = validate_vin(EXAMPLE_VIN + "0")  # 18 chars
        self.assertTrue(any("Length" in e for e in errors))

    def test_forbidden_i(self):
        vin = list(EXAMPLE_VIN)
        vin[-1] = "I"
        errors = validate_vin("".join(vin))
        self.assertTrue(any("forbidden" in e.lower() for e in errors))

    def test_forbidden_o(self):
        vin = list(EXAMPLE_VIN)
        vin[-1] = "O"
        errors = validate_vin("".join(vin))
        self.assertTrue(any("forbidden" in e.lower() for e in errors))

    def test_forbidden_q(self):
        vin = list(EXAMPLE_VIN)
        vin[-1] = "Q"
        errors = validate_vin("".join(vin))
        self.assertTrue(any("forbidden" in e.lower() for e in errors))

    def test_bad_check_digit(self):
        vin = list(EXAMPLE_VIN)
        vin[8] = "5"  # corrupt the check digit at index 8
        errors = validate_vin("".join(vin))
        self.assertTrue(any("Check digit" in e for e in errors))


# ---------------------------------------------------------------------------
# add_vehicle
# ---------------------------------------------------------------------------

class TestAddVehicle(unittest.TestCase):

    def setUp(self):
        self.store = _tmp_store()

    def tearDown(self):
        if os.path.exists(self.store):
            os.unlink(self.store)

    def test_add_creates_record(self):
        record = add_vehicle(EXAMPLE_VIN, self.store)
        self.assertEqual(record["vin"], EXAMPLE_VIN)

    def test_add_decodes_wmi(self):
        record = add_vehicle(EXAMPLE_VIN, self.store)
        self.assertEqual(record["wmi"], "3MZ")

    def test_add_decodes_country(self):
        record = add_vehicle(EXAMPLE_VIN, self.store)
        self.assertEqual(record["country_of_origin"], "Mexico")

    def test_add_decodes_possible_years(self):
        record = add_vehicle(EXAMPLE_VIN, self.store)
        self.assertIn(2015, record["possible_years"])
        self.assertIn(1985, record["possible_years"])

    def test_add_decodes_assembly_plant(self):
        record = add_vehicle(EXAMPLE_VIN, self.store)
        self.assertEqual(record["assembly_plant"], "M")

    def test_add_decodes_serial_number(self):
        record = add_vehicle(EXAMPLE_VIN, self.store)
        self.assertEqual(record["serial_number"], "131942")

    def test_add_user_fields_initially_none(self):
        record = add_vehicle(EXAMPLE_VIN, self.store)
        for field in UPDATABLE_FIELDS:
            self.assertIsNone(record[field], msg=f"Expected {field} to be None")

    def test_add_persists_to_file(self):
        add_vehicle(EXAMPLE_VIN, self.store)
        self.assertTrue(os.path.exists(self.store))
        with open(self.store) as fh:
            data = json.load(fh)
        self.assertIn(EXAMPLE_VIN, data)

    def test_add_duplicate_raises_value_error(self):
        add_vehicle(EXAMPLE_VIN, self.store)
        with self.assertRaises(ValueError):
            add_vehicle(EXAMPLE_VIN, self.store)

    def test_add_invalid_vin_raises_value_error(self):
        with self.assertRaises(ValueError):
            add_vehicle("BADVIN", self.store)

    def test_add_lowercase_vin_normalised(self):
        record = add_vehicle(EXAMPLE_VIN.lower(), self.store)
        self.assertEqual(record["vin"], EXAMPLE_VIN)


# ---------------------------------------------------------------------------
# update_vehicle
# ---------------------------------------------------------------------------

class TestUpdateVehicle(unittest.TestCase):

    def setUp(self):
        self.store = _tmp_store()
        add_vehicle(EXAMPLE_VIN, self.store)

    def tearDown(self):
        if os.path.exists(self.store):
            os.unlink(self.store)

    def test_update_owner(self):
        record = update_vehicle(EXAMPLE_VIN, "owner", "Jane Smith", self.store)
        self.assertEqual(record["owner"], "Jane Smith")

    def test_update_persists(self):
        update_vehicle(EXAMPLE_VIN, "owner", "Jane Smith", self.store)
        with open(self.store) as fh:
            data = json.load(fh)
        self.assertEqual(data[EXAMPLE_VIN]["owner"], "Jane Smith")

    def test_update_mileage_coerced_to_int(self):
        record = update_vehicle(EXAMPLE_VIN, "mileage", "45230", self.store)
        self.assertIsInstance(record["mileage"], int)
        self.assertEqual(record["mileage"], 45230)

    def test_update_mileage_bad_value_raises(self):
        with self.assertRaises(ValueError):
            update_vehicle(EXAMPLE_VIN, "mileage", "not-a-number", self.store)

    def test_update_color(self):
        record = update_vehicle(EXAMPLE_VIN, "color", "Soul Red Crystal", self.store)
        self.assertEqual(record["color"], "Soul Red Crystal")

    def test_update_purchase_date(self):
        record = update_vehicle(EXAMPLE_VIN, "purchase_date", "2021-06-15", self.store)
        self.assertEqual(record["purchase_date"], "2021-06-15")

    def test_update_license_plate(self):
        record = update_vehicle(EXAMPLE_VIN, "license_plate", "ABC-1234", self.store)
        self.assertEqual(record["license_plate"], "ABC-1234")

    def test_update_nickname(self):
        record = update_vehicle(EXAMPLE_VIN, "nickname", "Zoom-Zoom", self.store)
        self.assertEqual(record["nickname"], "Zoom-Zoom")

    def test_update_notes(self):
        record = update_vehicle(EXAMPLE_VIN, "notes", "Needs oil change.", self.store)
        self.assertEqual(record["notes"], "Needs oil change.")

    def test_update_unknown_field_raises(self):
        with self.assertRaises(ValueError):
            update_vehicle(EXAMPLE_VIN, "engine_size", "2.0L", self.store)

    def test_update_unknown_vin_raises(self):
        with self.assertRaises(KeyError):
            update_vehicle("1HGBH41JXMN109186", "owner", "Bob", self.store)

    def test_update_refreshes_updated_at(self):
        before = get_vehicle(EXAMPLE_VIN, self.store)["updated_at"]
        import time; time.sleep(1)
        after_record = update_vehicle(EXAMPLE_VIN, "owner", "Alice", self.store)
        # updated_at may be equal if the OS clock resolution is low, but must
        # not be earlier than created_at.
        self.assertGreaterEqual(after_record["updated_at"], before)

    def test_all_updatable_fields_accepted(self):
        for field in UPDATABLE_FIELDS:
            if field == "mileage":
                update_vehicle(EXAMPLE_VIN, field, "1000", self.store)
            else:
                update_vehicle(EXAMPLE_VIN, field, f"test-{field}", self.store)
        record = get_vehicle(EXAMPLE_VIN, self.store)
        self.assertEqual(record["mileage"], 1000)


# ---------------------------------------------------------------------------
# get_vehicle
# ---------------------------------------------------------------------------

class TestGetVehicle(unittest.TestCase):

    def setUp(self):
        self.store = _tmp_store()
        add_vehicle(EXAMPLE_VIN, self.store)

    def tearDown(self):
        if os.path.exists(self.store):
            os.unlink(self.store)

    def test_get_returns_record(self):
        record = get_vehicle(EXAMPLE_VIN, self.store)
        self.assertEqual(record["vin"], EXAMPLE_VIN)

    def test_get_lowercase_vin_normalised(self):
        record = get_vehicle(EXAMPLE_VIN.lower(), self.store)
        self.assertEqual(record["vin"], EXAMPLE_VIN)

    def test_get_unknown_vin_raises_key_error(self):
        with self.assertRaises(KeyError):
            get_vehicle("1HGBH41JXMN109186", self.store)


# ---------------------------------------------------------------------------
# list_vehicles
# ---------------------------------------------------------------------------

class TestListVehicles(unittest.TestCase):

    def setUp(self):
        self.store = _tmp_store()

    def tearDown(self):
        if os.path.exists(self.store):
            os.unlink(self.store)

    def test_empty_store_returns_empty_list(self):
        self.assertEqual(list_vehicles(self.store), [])

    def test_list_returns_all_records(self):
        add_vehicle(EXAMPLE_VIN, self.store)
        # Add a second VIN (different, but valid): well-known SAE test vector
        add_vehicle("1M8GDM9AXKP042788", self.store)
        vehicles = list_vehicles(self.store)
        self.assertEqual(len(vehicles), 2)

    def test_list_sorted_by_vin(self):
        add_vehicle("1M8GDM9AXKP042788", self.store)
        add_vehicle(EXAMPLE_VIN, self.store)
        vins = [r["vin"] for r in list_vehicles(self.store)]
        self.assertEqual(vins, sorted(vins))


# ---------------------------------------------------------------------------
# remove_vehicle
# ---------------------------------------------------------------------------

class TestRemoveVehicle(unittest.TestCase):

    def setUp(self):
        self.store = _tmp_store()
        add_vehicle(EXAMPLE_VIN, self.store)

    def tearDown(self):
        if os.path.exists(self.store):
            os.unlink(self.store)

    def test_remove_returns_record(self):
        record = remove_vehicle(EXAMPLE_VIN, self.store)
        self.assertEqual(record["vin"], EXAMPLE_VIN)

    def test_remove_deletes_from_store(self):
        remove_vehicle(EXAMPLE_VIN, self.store)
        with self.assertRaises(KeyError):
            get_vehicle(EXAMPLE_VIN, self.store)

    def test_remove_unknown_vin_raises_key_error(self):
        with self.assertRaises(KeyError):
            remove_vehicle("1HGBH41JXMN109186", self.store)


if __name__ == "__main__":
    unittest.main(verbosity=2)

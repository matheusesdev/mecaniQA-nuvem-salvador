import math
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from app import (
    Settings,
    iot_processing_errors_total,
    iot_readings_in_progress,
    iot_readings_total,
    iot_sensor_faults_total,
    iot_sensor_value,
    load_settings,
    peak_is_active,
    process_reading,
)


class SimulatorTests(unittest.TestCase):
    def test_valid_reading_updates_counter_and_latest_value(self):
        before = iot_readings_total.labels(sensor_type="temperature")._value.get()
        process_reading(
            {"sensor_type": "temperature", "value": 93.5, "fault": False}
        )

        self.assertEqual(
            iot_readings_total.labels(sensor_type="temperature")._value.get(),
            before + 1,
        )
        self.assertEqual(
            iot_sensor_value.labels(sensor_type="temperature")._value.get(), 93.5
        )
        self.assertEqual(iot_readings_in_progress._value.get(), 0)

    def test_simulated_fault_is_counted_separately(self):
        readings_before = iot_readings_total.labels(sensor_type="electrical")._value.get()
        faults_before = iot_sensor_faults_total.labels(sensor_type="electrical")._value.get()
        errors_before = iot_processing_errors_total._value.get()
        process_reading(
            {"sensor_type": "electrical", "value": 10.5, "fault": True}
        )

        self.assertEqual(
            iot_readings_total.labels(sensor_type="electrical")._value.get(),
            readings_before + 1,
        )
        self.assertEqual(
            iot_sensor_faults_total.labels(sensor_type="electrical")._value.get(),
            faults_before + 1,
        )
        self.assertEqual(iot_processing_errors_total._value.get(), errors_before)

    def test_invalid_reading_counts_error_without_valid_reading(self):
        readings_before = iot_readings_total.labels(sensor_type="temperature")._value.get()
        errors_before = iot_processing_errors_total._value.get()

        with self.assertRaisesRegex(ValueError, "finite number"):
            process_reading(
                {"sensor_type": "temperature", "value": math.nan, "fault": False}
            )

        self.assertEqual(iot_processing_errors_total._value.get(), errors_before + 1)
        self.assertEqual(
            iot_readings_total.labels(sensor_type="temperature")._value.get(),
            readings_before,
        )
        self.assertEqual(iot_readings_in_progress._value.get(), 0)

    def test_in_progress_returns_to_zero_after_unexpected_error(self):
        invalid_reading = {"sensor_type": "temperature", "value": 90, "fault": "yes"}
        with self.assertRaisesRegex(ValueError, "boolean"):
            process_reading(invalid_reading)
        self.assertEqual(iot_readings_in_progress._value.get(), 0)

    def test_settings_are_validated(self):
        settings = load_settings(
            {
                "READINGS_PER_SECOND": "2.5",
                "PEAK_MULTIPLIER": "4",
                "PEAK_MODE": "always",
            }
        )
        self.assertEqual(settings, Settings(2.5, 4, "always"))
        for invalid_rate in ("0", "-1", "NaN", "Infinity", "not-a-number"):
            with self.subTest(rate=invalid_rate), self.assertRaises(ValueError):
                load_settings({"READINGS_PER_SECOND": invalid_rate})
        with self.assertRaisesRegex(ValueError, "PEAK_MODE"):
            load_settings({"PEAK_MODE": "sometimes"})
        with self.assertRaisesRegex(ValueError, "must be finite"):
            load_settings(
                {"READINGS_PER_SECOND": "1e308", "PEAK_MULTIPLIER": "10"}
            )
        with self.assertRaisesRegex(ValueError, "too small"):
            load_settings({"READINGS_PER_SECOND": "1e-320"})

    def test_scheduled_peak_uses_sao_paulo_ten_minute_windows(self):
        sao_paulo = ZoneInfo("America/Sao_Paulo")
        self.assertTrue(
            peak_is_active("scheduled", datetime(2026, 1, 1, 8, 9, tzinfo=sao_paulo))
        )
        self.assertTrue(peak_is_active("scheduled", datetime(2026, 1, 1, 8, 9)))
        self.assertFalse(
            peak_is_active("scheduled", datetime(2026, 1, 1, 8, 10, tzinfo=sao_paulo))
        )
        self.assertTrue(
            peak_is_active("scheduled", datetime(2026, 1, 1, 17, 0, tzinfo=sao_paulo))
        )
        self.assertFalse(
            peak_is_active("scheduled", datetime(2026, 1, 1, 16, 59, tzinfo=sao_paulo))
        )
        self.assertTrue(peak_is_active("always"))
        self.assertFalse(peak_is_active("off"))


if __name__ == "__main__":
    unittest.main()

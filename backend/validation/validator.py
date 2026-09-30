from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger("validation_service")

# Standard physical & agronomic boundaries
METRIC_BOUNDARIES = {
    "temperature": {"min": -10.0, "max": 60.0, "unit": "°C", "agronomic_optimal": (15.0, 35.0)},
    "humidity": {"min": 0.0, "max": 100.0, "unit": "%", "agronomic_optimal": (40.0, 95.0)},
    "moisture": {"min": 0.0, "max": 100.0, "unit": "%", "agronomic_optimal": (20.0, 85.0)},
    "ph": {"min": 0.0, "max": 14.0, "unit": "pH", "agronomic_optimal": (4.5, 9.0)},
    "soil_moisture": {"min": 0.0, "max": 100.0, "unit": "%", "agronomic_optimal": (20.0, 85.0)}
}

KNOWN_CROPS = {"tomato", "potato", "bell pepper", "wheat", "rice", "maize"}

class SensorValidationService:
    def __init__(self):
        self.rejected_records = []
        self.accepted_records = []

    def validate_reading(self, reading: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        metric = reading.get("metric", "").lower().strip()
        val = reading.get("value")
        sensor_id = reading.get("sensor_id", "UNKNOWN")

        if val is None:
            return False, "Missing required numeric measurement value.", "Rejected: Null value detected"

        try:
            val_float = float(val)
        except (ValueError, TypeError):
            return False, f"Non-numeric sensor reading: {val}", "Rejected: Parse error"

        if metric in METRIC_BOUNDARIES:
            bounds = METRIC_BOUNDARIES[metric]
            if val_float < bounds["min"] or val_float > bounds["max"]:
                reason = f"Value {val_float}{bounds['unit']} outside valid physical range ({bounds['min']} to {bounds['max']}{bounds['unit']}). Possible sensor breakdown or telemetry corruption."
                action = "Excluded from graph reasoning and risk computation."
                return False, reason, action

        crop_context = reading.get("crop", "")
        if crop_context and crop_context.lower() not in KNOWN_CROPS:
            return False, f"Unknown agricultural crop reference '{crop_context}' in sensor telemetry packet.", "Flagged: Unrecognized agronomic entity"

        return True, None, "Accepted into agricultural knowledge reasoning"

    def process_readings(self, readings_list: list) -> Dict[str, Any]:
        self.rejected_records = []
        self.accepted_records = []

        for r in readings_list:
            is_valid, reason, action = self.validate_reading(r)
            record_copy = dict(r)
            if not is_valid:
                record_copy["status"] = "INVALID"
                record_copy["anomaly_reason"] = reason
                record_copy["action_taken"] = action
                self.rejected_records.append(record_copy)
            else:
                record_copy["status"] = "VALID"
                record_copy["action_taken"] = action
                self.accepted_records.append(record_copy)

        return {
            "total_processed": len(readings_list),
            "valid_count": len(self.accepted_records),
            "invalid_count": len(self.rejected_records),
            "valid_records": self.accepted_records,
            "invalid_records": self.rejected_records
        }

validation_service = SensorValidationService()

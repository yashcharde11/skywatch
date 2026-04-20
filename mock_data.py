"""
Simulated Data for Drone Security Analyst Agent
"""

# ─── Simulated Video Frame Data ────────────────────────────────────────────────

SIMULATED_FRAMES = [
    {"time": "00:00", "location": "Main Gate", "description": "Frame 1: Empty driveway, no activity detected."},
    {"time": "00:01", "location": "Main Gate", "description": "Frame 2: Person loitering near main gate, wearing dark hoodie."},
    {"time": "00:05", "location": "Parking Lot", "description": "Frame 3: Blue Ford F150 truck entering parking lot from north entrance."},
    {"time": "00:12", "location": "Garage", "description": "Frame 4: Blue Ford F150 parked at garage bay 2. Engine off."},
    {"time": "00:20", "location": "Perimeter", "description": "Frame 5: Motion detected along east perimeter fence. Appears to be a small animal (possibly raccoon)."},
    {"time": "00:35", "location": "Main Gate", "description": "Frame 6: Unknown individual approaching main gate, no badge visible."},
    {"time": "00:42", "location": "Main Gate", "description": "Frame 7: Unknown individual still at main gate. Appears to be using phone."},
    {"time": "01:00", "location": "Parking Lot", "description": "Frame 8: Blue Ford F150 exits parking lot, heading south."},
    {"time": "01:15", "location": "Rooftop", "description": "Frame 9: Rooftop access door ajar. No personnel visible."},
    {"time": "01:20", "location": "Rooftop", "description": "Frame 10: Two individuals on rooftop, no safety harnesses, tools visible."},
    {"time": "02:00", "location": "Parking Lot", "description": "Frame 11: Blue Ford F150 re-enters parking lot. Second visit today."},
    {"time": "02:15", "location": "Garage", "description": "Frame 12: Blue Ford F150 docked at garage bay 2 again. Unloading cargo."},
    {"time": "03:00", "location": "Perimeter", "description": "Frame 13: Large delivery vehicle (white van) near service entrance."},
    {"time": "03:10", "location": "Service Entrance", "description": "Frame 14: White cargo van, license plate partially obscured, driver exits."},
    {"time": "04:00", "location": "Main Gate", "description": "Frame 15: All clear. No activity detected at main gate."},
]

# ─── Telemetry Data ─────────────────────────────────────────────────────────────

TELEMETRY_DATA = [
    {"time": "00:00", "lat": 37.7749, "lon": -122.4194, "altitude_m": 50, "battery_pct": 98, "speed_mps": 0.0, "zone": "Dock"},
    {"time": "00:01", "lat": 37.7750, "lon": -122.4193, "altitude_m": 55, "battery_pct": 97, "speed_mps": 2.5, "zone": "Main Gate"},
    {"time": "00:05", "lat": 37.7752, "lon": -122.4190, "altitude_m": 60, "battery_pct": 95, "speed_mps": 3.1, "zone": "Parking Lot"},
    {"time": "00:12", "lat": 37.7753, "lon": -122.4188, "altitude_m": 45, "battery_pct": 92, "speed_mps": 1.2, "zone": "Garage"},
    {"time": "00:20", "lat": 37.7748, "lon": -122.4198, "altitude_m": 58, "battery_pct": 90, "speed_mps": 4.0, "zone": "Perimeter"},
    {"time": "00:35", "lat": 37.7750, "lon": -122.4193, "altitude_m": 52, "battery_pct": 87, "speed_mps": 0.5, "zone": "Main Gate"},
    {"time": "01:00", "lat": 37.7752, "lon": -122.4190, "altitude_m": 60, "battery_pct": 83, "speed_mps": 2.8, "zone": "Parking Lot"},
    {"time": "01:15", "lat": 37.7755, "lon": -122.4185, "altitude_m": 70, "battery_pct": 80, "speed_mps": 3.5, "zone": "Rooftop"},
    {"time": "02:00", "lat": 37.7752, "lon": -122.4190, "altitude_m": 60, "battery_pct": 72, "speed_mps": 2.9, "zone": "Parking Lot"},
    {"time": "03:00", "lat": 37.7748, "lon": -122.4199, "altitude_m": 55, "battery_pct": 61, "speed_mps": 2.2, "zone": "Perimeter"},
    {"time": "04:00", "lat": 37.7749, "lon": -122.4194, "altitude_m": 50, "battery_pct": 55, "speed_mps": 0.0, "zone": "Dock"},
]

# ─── Mock AI Analyses (For Unit Tests) ──────────────────────────────────────────

MOCK_ANALYSES = {
    0: {"objects": ["empty driveway"], "event_type": "normal", "threat_level": "low", "summary": "No activity at main gate", "alert": None, "log_entry": "No activity at Main Gate, 00:00."},
    1: {"objects": ["person", "dark hoodie"], "event_type": "person", "threat_level": "high", "summary": "Suspicious person loitering at main gate", "alert": "Person loitering at main gate, 00:01.", "log_entry": "Person in dark hoodie spotted loitering at Main Gate, 00:01."},
    2: {"objects": ["Blue Ford F150", "truck"], "event_type": "vehicle", "threat_level": "low", "summary": "Blue Ford F150 entered parking lot", "alert": None, "log_entry": "Blue Ford F150 spotted entering Parking Lot, 00:05."},
    3: {"objects": ["Blue Ford F150", "garage"], "event_type": "vehicle", "threat_level": "low", "summary": "Blue Ford F150 parked at garage", "alert": None, "log_entry": "Blue Ford F150 parked at Garage bay 2, 00:12."},
    5: {"objects": ["unknown individual"], "event_type": "intrusion", "threat_level": "high", "summary": "Unknown individual at main gate without badge", "alert": "Unidentified person at main gate without badge, 00:35.", "log_entry": "Unknown individual at Main Gate, no badge visible, 00:35."},
    9: {"objects": ["two individuals", "tools", "rooftop"], "event_type": "safety_violation", "threat_level": "critical", "summary": "Safety violation on rooftop - no harnesses", "alert": "SAFETY VIOLATION: Two individuals on rooftop without harnesses, 01:20.", "log_entry": "Safety violation: two individuals on rooftop without safety harnesses, 01:20."},
    10: {"objects": ["Blue Ford F150"], "event_type": "vehicle", "threat_level": "medium", "summary": "Blue Ford F150 returned for second visit", "alert": "Blue Ford F150 second entry today - flagged for review, 02:00.", "log_entry": "Blue Ford F150 re-entered Parking Lot (2nd visit), 02:00."},
}

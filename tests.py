"""
Test Suite for Drone Security Analyst Agent
Tests: frame indexing, alert generation, query system, AI analysis
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from mock_data import SIMULATED_FRAMES, TELEMETRY_DATA, MOCK_ANALYSES
from frame_index import FrameIndex


def populate_mock_index() -> FrameIndex:
    """Populate frame index with mock data for testing."""
    index = FrameIndex()
    telemetry_map = {t["time"]: t for t in TELEMETRY_DATA}
    default_t = TELEMETRY_DATA[0]
    
    for i, frame in enumerate(SIMULATED_FRAMES):
        analysis = MOCK_ANALYSES.get(i, {
            "objects": ["scene"], "event_type": "normal", "threat_level": "low",
            "summary": frame["description"], "alert": None,
            "log_entry": f"Routine observation at {frame['location']}, {frame['time']}."
        })
        record = index.index_frame(
            frame_id=i+1,
            timestamp=frame["time"],
            location=frame["location"],
            raw_description=frame["description"],
            ai_analysis=analysis
        )
        index.log_event({"frame_id": i+1, "time": frame["time"], 
                          "location": frame["location"],
                          "log": analysis["log_entry"], 
                          "threat_level": analysis["threat_level"]})
        if analysis.get("alert"):
            index.add_alert({
                "frame_id": i+1, "time": frame["time"],
                "location": frame["location"], "message": analysis["alert"],
                "threat_level": analysis["threat_level"],
                "objects": analysis["objects"]
            })
    return index


# ─── Test Cases ──────────────────────────────────────────────────────────────

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def run_test(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"{status} | {name}"
    if detail:
        msg += f"\n         → {detail}"
    print(msg)
    results.append((name, condition))
    return condition


def test_frame_indexing(index: FrameIndex):
    print("\n── TEST GROUP: Frame Indexing ──────────────────────────")
    
    run_test("All 15 frames indexed",
             len(index.frames) == 15,
             f"Found {len(index.frames)} frames")
    
    # Check F150 was logged
    f150_frames = [f for f in index.frames if "Blue Ford F150" in str(f["objects_detected"])]
    run_test("Blue Ford F150 logged correctly (≥2 frames)",
             len(f150_frames) >= 2,
             f"Found {len(f150_frames)} F150 frames: {[f['timestamp'] for f in f150_frames]}")
    
    # Check log entries exist
    logs_with_content = [f for f in index.frames if f["summary"]]
    run_test("All frames have non-empty summary",
             len(logs_with_content) == 15,
             f"{len(logs_with_content)}/15 frames have summaries")
    
    # Check timestamps
    has_timestamps = all(f["timestamp"] for f in index.frames)
    run_test("All frames have timestamps", has_timestamps)
    
    # Check locations
    locations = set(f["location"] for f in index.frames)
    run_test("Multiple locations indexed",
             len(locations) >= 3,
             f"Locations: {sorted(locations)}")


def test_alert_generation(index: FrameIndex):
    print("\n── TEST GROUP: Alert Generation ────────────────────────")
    
    run_test("Alerts were generated",
             len(index.alerts) > 0,
             f"Total alerts: {len(index.alerts)}")
    
    # Person loitering alert
    loitering_alerts = [a for a in index.alerts 
                        if "loiter" in a["message"].lower() or "person" in a["message"].lower()]
    run_test("Person loitering alert triggered",
             len(loitering_alerts) > 0,
             f"Alert: {loitering_alerts[0]['message'] if loitering_alerts else 'None'}")
    
    # High threat alerts
    high_alerts = [a for a in index.alerts if a["threat_level"] in ["high", "critical"]]
    run_test("High/critical threat alerts generated",
             len(high_alerts) >= 1,
             f"High threat alerts: {len(high_alerts)}")
    
    # F150 second visit alert
    f150_alerts = [a for a in index.alerts if "F150" in a["message"] or "truck" in a["message"].lower()]
    run_test("Vehicle repeat-visit alert triggered",
             len(f150_alerts) >= 1,
             f"Vehicle alert: {f150_alerts[0]['message'] if f150_alerts else 'None found, checking...'}")
    
    # Safety violation
    safety_alerts = [a for a in index.alerts if "safety" in a["message"].lower() or "harness" in a["message"].lower()]
    run_test("Safety violation alert generated",
             len(safety_alerts) >= 1,
             f"Safety alert: {safety_alerts[0]['message'] if safety_alerts else 'None'}")


def test_query_system(index: FrameIndex):
    print("\n── TEST GROUP: Query / Indexing System ─────────────────")
    
    # Query by object
    truck_results = index.query_by_object("ford")
    run_test("Query by object ('ford') returns results",
             len(truck_results) >= 1,
             f"Found {len(truck_results)} frame(s) with Ford")
    
    person_results = index.query_by_object("person")
    run_test("Query by object ('person') returns results",
             len(person_results) >= 1,
             f"Found {len(person_results)} frame(s) with person")
    
    # Query by location
    gate_results = index.query_by_location("Main Gate")
    run_test("Query by location ('Main Gate') returns results",
             len(gate_results) >= 1,
             f"Found {len(gate_results)} frame(s) at Main Gate")
    
    # Query by threat level
    high_results = index.query_by_threat_level("high")
    run_test("Query by threat level ('high') returns results",
             len(high_results) >= 1,
             f"Found {len(high_results)} high-threat frame(s)")
    
    # Query by time range
    time_results = index.query_by_time_range("00:00", "00:30")
    run_test("Query by time range (00:00-00:30) returns results",
             len(time_results) >= 1,
             f"Found {len(time_results)} frame(s) in time range")
    
    # Empty query returns empty
    nothing = index.query_by_object("helicopter_that_doesnt_exist")
    run_test("Query for nonexistent object returns empty list",
             len(nothing) == 0)


def test_stats_and_log(index: FrameIndex):
    print("\n── TEST GROUP: Stats & Event Log ───────────────────────")
    
    stats = index.get_summary_stats()
    
    run_test("Stats report total_frames = 15",
             stats["total_frames"] == 15,
             str(stats))
    
    run_test("Stats report total_alerts > 0",
             stats["total_alerts"] > 0)
    
    run_test("Stats report objects_frequency dict populated",
             isinstance(stats["objects_frequency"], dict) and len(stats["objects_frequency"]) > 0,
             f"Objects: {list(stats['objects_frequency'].keys())[:5]}")
    
    run_test("Event log has 15 entries",
             len(index.event_log) == 15)
    
    # Check a specific known log entry format
    logs = [e["log"] for e in index.event_log if e["log"]]
    run_test("Event log entries are non-empty strings",
             len(logs) > 10,
             f"Sample log: {logs[0] if logs else 'None'}")


def test_export(index: FrameIndex):
    print("\n── TEST GROUP: Export & Serialization ──────────────────")
    
    data = index.export()
    
    run_test("Export contains 'frames' key", "frames" in data)
    run_test("Export contains 'alerts' key", "alerts" in data)
    run_test("Export contains 'event_log' key", "event_log" in data)
    run_test("Export contains 'stats' key", "stats" in data)
    
    # Should be JSON-serializable
    try:
        json_str = json.dumps(data)
        run_test("Export is JSON-serializable", True, f"{len(json_str)} bytes")
    except Exception as e:
        run_test("Export is JSON-serializable", False, str(e))


# ─── Run All Tests ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  DRONE SECURITY ANALYST AGENT — TEST SUITE")
    print("=" * 60)
    
    index = populate_mock_index()
    
    test_frame_indexing(index)
    test_alert_generation(index)
    test_query_system(index)
    test_stats_and_log(index)
    test_export(index)
    
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"  RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("  🎉 ALL TESTS PASSED")
    else:
        failed = [(name, ok) for name, ok in results if not ok]
        print(f"  ⚠ FAILED TESTS:")
        for name, _ in failed:
            print(f"    - {name}")
    print("=" * 60)
    
    sys.exit(0 if passed == total else 1)
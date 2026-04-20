"""
Frame Index Data Structure (In-Memory DB)
"""

from datetime import datetime

class FrameIndex:
    """Simple frame-by-frame indexing system with queryable metadata."""
    
    def __init__(self):
        self.frames = []  # List of indexed frame records
        self.alerts = []  # Generated alerts
        self.event_log = []  # Structured event log
    
    def index_frame(self, frame_id: int, timestamp: str, location: str, 
                    raw_description: str, ai_analysis: dict, telemetry: dict = None):
        """Index a processed frame with AI analysis results."""
        record = {
            "frame_id": frame_id,
            "timestamp": timestamp,
            "location": location,
            "raw_description": raw_description,
            "objects_detected": ai_analysis.get("objects", []),
            "event_type": ai_analysis.get("event_type", "normal"),
            "threat_level": ai_analysis.get("threat_level", "low"),
            "summary": ai_analysis.get("summary", ""),
            "indexed_at": datetime.now().isoformat(),
            "telemetry": telemetry or {}
        }
        self.frames.append(record)
        return record
    
    def add_alert(self, alert: dict):
        self.alerts.append(alert)
    
    def log_event(self, event: dict):
        self.event_log.append(event)
    
    def load_from_dict(self, data: dict):
        """Populate the FrameIndex from a dictionary (e.g., loaded from JSON)."""
        self.frames = data.get("frames", [])
        self.alerts = data.get("alerts", [])
        self.event_log = data.get("event_log", [])

    def query_by_object(self, object_type: str) -> list:
        """Query frames containing a specific object."""
        return [f for f in self.frames 
                if any(object_type.lower() in str(obj).lower() 
                       for obj in f.get("objects_detected", []))]
    
    def query_by_location(self, location: str) -> list:
        return [f for f in self.frames 
                if location.lower() in f.get("location", "").lower()]
    
    def query_by_threat_level(self, level: str) -> list:
        return [f for f in self.frames if f.get("threat_level") == level]
    
    def query_by_time_range(self, start: str, end: str) -> list:
        return [f for f in self.frames 
                if start <= f.get("timestamp", "") <= end]
    
    def get_telemetry_history(self) -> list:
        """Retrieve the full telemetry and path history of the patrol."""
        return [{
            "timestamp": f.get("timestamp", "unknown"), 
            "location": f.get("location", "unknown"), 
            "telemetry": f.get("telemetry", {})
        } for f in self.frames]
    
    def get_summary_stats(self) -> dict:
        total = len(self.frames)
        threats = len([f for f in self.frames if f.get("threat_level") in ["high", "critical"]])
        objects_seen = {}
        for f in self.frames:
            for obj in f.get("objects_detected", []):
                objects_seen[obj] = objects_seen.get(obj, 0) + 1
        return {
            "total_frames": total,
            "total_alerts": len(self.alerts),
            "high_threat_frames": threats,
            "objects_frequency": objects_seen
        }
    
    def to_llm_context(self) -> str:
        """Generates a token-efficient text representation of the patrol data."""
        lines = ["=== DRONE PATROL DATA CONTEXT ==="]
        
        stats = self.get_summary_stats()
        lines.append(f"Total Frames: {stats['total_frames']} | Alerts: {stats['total_alerts']} | High Threat: {stats['high_threat_frames']}")
        
        lines.append("\n-- TIMELINE & TELEMETRY --")
        for f in self.frames:
            t = f.get("telemetry", {})
            lines.append(f"[{f.get('timestamp', 'N/A')}] Loc: {f.get('location', 'N/A')} | Alt: {t.get('altitude_m', 'N/A')}m | Bat: {t.get('battery_pct', 'N/A')}% | Spd: {t.get('speed_mps', 'N/A')}m/s | Event: {f.get('summary', '')}")
            
        if self.alerts:
            lines.append("\n-- ALERTS --")
            for a in self.alerts:
                lines.append(f"[{a.get('time', 'N/A')}] THREAT {a.get('threat_level', 'low').upper()}: {a.get('message', 'No detail provided.')}")
                
        return "\n".join(lines)
    
    def export(self) -> dict:
        return {
            "frames": self.frames,
            "alerts": self.alerts,
            "event_log": self.event_log,
            "stats": self.get_summary_stats(),
            "telemetry_history": self.get_telemetry_history()
        }

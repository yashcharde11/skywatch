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
                    raw_description: str, ai_analysis: dict):
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
            "indexed_at": datetime.now().isoformat()
        }
        self.frames.append(record)
        return record
    
    def add_alert(self, alert: dict):
        self.alerts.append(alert)
    
    def log_event(self, event: dict):
        self.event_log.append(event)
    
    def query_by_object(self, object_type: str) -> list:
        """Query frames containing a specific object."""
        return [f for f in self.frames 
                if any(object_type.lower() in obj.lower() 
                       for obj in f["objects_detected"])]
    
    def query_by_location(self, location: str) -> list:
        return [f for f in self.frames 
                if location.lower() in f["location"].lower()]
    
    def query_by_threat_level(self, level: str) -> list:
        return [f for f in self.frames if f["threat_level"] == level]
    
    def query_by_time_range(self, start: str, end: str) -> list:
        return [f for f in self.frames 
                if start <= f["timestamp"] <= end]
    
    def get_summary_stats(self) -> dict:
        total = len(self.frames)
        threats = len([f for f in self.frames if f["threat_level"] in ["high", "critical"]])
        objects_seen = {}
        for f in self.frames:
            for obj in f["objects_detected"]:
                objects_seen[obj] = objects_seen.get(obj, 0) + 1
        return {
            "total_frames": total,
            "total_alerts": len(self.alerts),
            "high_threat_frames": threats,
            "objects_frequency": objects_seen
        }
    
    def export(self) -> dict:
        return {
            "frames": self.frames,
            "alerts": self.alerts,
            "event_log": self.event_log,
            "stats": self.get_summary_stats()
        }

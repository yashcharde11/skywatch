# System Architecture — Drone Security Analyst Agent

## High-Level Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                         DRONE SECURITY AGENT                          │
│                                                                        │
│   INPUT SOURCES                 PROCESSING LAYER           OUTPUTS    │
│   ─────────────                 ────────────────           ───────    │
│                                                                        │
│   ┌───────────┐                 ┌────────────────┐                    │
│   │  Telemetry│──────────────▶  │                │   ┌─────────────┐ │
│   │  Simulator│                 │   AI Agent     │──▶│ Frame Index │ │
│   └───────────┘                 │   (Claude      │   │             │ │
│                                 │    claude-     │   │ ·frame_id   │ │
│   ┌───────────┐                 │    sonnet-4)   │   │ ·timestamp  │ │
│   │  Video    │──────────────▶  │                │   │ ·location   │ │
│   │  Frames   │                 │   ·analyze()   │   │ ·objects    │ │
│   │(Simulated)│                 │   ·alert()     │   │ ·threat     │ │
│   └───────────┘                 │   ·summarize() │   │ ·summary    │ │
│                                 │   ·answer()    │   └─────────────┘ │
│   ┌───────────┐                 │                │                    │
│   │ Context   │──────────────▶  │   Context      │   ┌─────────────┐ │
│   │ History   │                 │   Window       │──▶│ Alert Feed  │ │
│   │ (last 5)  │                 │   (5 events)   │   │             │ │
│   └───────────┘                 └────────────────┘   └─────────────┘ │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

## Frame Processing Pipeline

```
Frame N arrives
      │
      ▼
┌─────────────┐
│ Get matching│
│  telemetry  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│     Claude AI Analysis          │
│                                 │
│  Input:                         │
│  - Frame description            │
│  - Telemetry (alt, battery,     │
│    speed, zone)                 │
│  - Last 5 events (context)      │
│                                 │
│  Output (structured JSON):      │
│  - objects[]                    │
│  - event_type                   │
│  - threat_level                 │
│  - summary                      │
│  - alert (null or string)       │
│  - log_entry                    │
└──────────────┬──────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐  ┌──────────────┐
│ Index Frame │  │ alert != null│
│ in FrameDB  │  │      ?       │
└─────────────┘  └──────┬───────┘
                        │ yes
                        ▼
                 ┌──────────────┐
                 │ Add to Alert │
                 │    Feed      │
                 └──────────────┘
                        │
                        ▼
               Update Context History
```

## FrameIndex Schema

```
FrameRecord {
  frame_id:         int          # 1-based sequential
  timestamp:        "HH:MM"      # Patrol time
  location:         string       # Zone name
  raw_description:  string       # Original simulated text
  objects_detected: string[]     # AI-extracted objects
  event_type:       enum         # normal|vehicle|person|intrusion|safety_violation
  threat_level:     enum         # low|medium|high|critical
  summary:          string       # One-sentence AI summary
  indexed_at:       ISO datetime # Wall clock time of indexing
}

AlertRecord {
  frame_id:     int
  time:         "HH:MM"
  location:     string
  message:      string          # Human-readable alert
  threat_level: enum
  objects:      string[]
}
```

## Alert Rules (Implicit, learned by Claude)

| Trigger | Threat Level |
|---------|-------------|
| Person loitering at night | HIGH |
| Unidentified person, no badge | HIGH |
| Safety violation (no harness, etc.) | CRITICAL |
| Vehicle second entry same day | MEDIUM |
| Obscured license plate | MEDIUM |
| Small animal motion | LOW |
| Normal traffic, identified vehicles | LOW |

## Query Capabilities

The FrameIndex supports four query axes:
- **By object** — `query_by_object("ford")` → all frames with Ford in objects[]
- **By location** — `query_by_location("Main Gate")` → all main gate frames
- **By threat level** — `query_by_threat_level("critical")` → critical frames only
- **By time range** — `query_by_time_range("00:00", "01:00")` → first hour frames

## Scalability Notes

For production at scale:
1. Replace in-memory FrameIndex with **ChromaDB** (semantic search) + **PostgreSQL** (structured queries)
2. Replace simulated frames with **RTSP stream** → OpenCV frame extraction → **BLIP-2** captions
3. Replace sequential processing with **async queue** (Celery + Redis) for parallel frame analysis
4. Add **vector embeddings** of frame summaries for similarity search ("find frames similar to this one")
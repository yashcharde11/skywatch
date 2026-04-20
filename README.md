# 🛸 Drone Security Analyst Agent

> AI-powered drone surveillance system that processes real-time telemetry and video frames to detect security events, generate alerts, and answer natural language questions about patrol activity.

---

## 📋 Feature Specification

**Value to Property Owners:** Autonomous drone surveillance that operates 24/7 without human oversight — automatically detecting threats, logging events with full context, and generating instant alerts when security rules are violated.

### Key Requirements
1. **Real-time Frame Analysis** — Process each video frame through a Vision-Language Model to identify objects (vehicles, people, packages) and classify events with threat levels (low/medium/high/critical).
2. **Context-Aware Alerting** — Generate alerts that incorporate patrol history (e.g., "Blue Ford F150 second entry today") rather than treating each frame in isolation.
3. **Queryable Frame Index** — Store every frame with metadata so operators can ask "show all truck events" or "what happened at the main gate after midnight?"

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  DRONE SECURITY AGENT                     │
│                                                           │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐ │
│  │  Telemetry  │───▶│   AI Agent   │───▶│  Frame Index│ │
│  │  Simulator  │    │ (LangGraph + │    │  (In-Memory │ │
│  └─────────────┘    │   Groq API)  │    │   Key-Value)│ │
│                            │            └─────────────┘ │
│  ┌─────────────┐           │            ┌─────────────┐ │
│  │    Video    │───────────┘            │  Alert      │ │
│  │   Frames    │                        │  Engine     │ │
│  │ (Simulated) │                        └─────────────┘ │
│  └─────────────┘                                         │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │              React Dashboard (Frontend)           │   │
│  │  Live View │ Frame Log │ Frame Search │ Ask AI    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Components
| Component | Role |
|-----------|------|
| `services/agent.py` | Core LangGraph supervisor, node definitions, and routing logic |
| `services/sub_agents/`| Specialized agents (Vision, Telemetry, Security, Data Ops, Red Team) |
| `prompts_loader.py` | Dynamic file loader for encapsulating sub-agent prompts |
| `server.py` | FastAPI REST + SSE streaming endpoint |
| `app.jsx` | React dashboard with live view, frame log, and @mention auto-complete chat |

### Data Flow
1. **Simulated frames** (text descriptions) + **telemetry** feed into the agent
2. The LLM (Llama 3 via Groq) analyzes each frame in context of the last 5 events
3. Structured JSON analysis is stored in the **FrameIndex** (keyed by frame_id, timestamp, location, threat_level, objects)
4. High-threat analyses trigger **alerts** (persisted separately)
5. Frontend streams events via SSE and renders the live dashboard

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Groq API key (get one at https://console.groq.com)

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install langchain-groq langgraph fastapi uvicorn python-dotenv

# Set your API key
export GROQ_API_KEY="gsk-..."  # Windows: set GROQ_API_KEY=gsk-...
```

### Run the CLI Agent (no frontend needed)

```bash
cd backend
python agent.py
# Outputs real-time logs, alerts, and saves patrol_results.json
```

### Run the Tests

```bash
cd backend
python tests.py
# Expected: 26/26 tests passed ✅
```

### Run the Full Stack (Backend + Frontend)

```bash
# Terminal 1: Start the API server
cd backend
uvicorn server:app --reload --port 8000

# Terminal 2: Start the React frontend
cd frontend
npm install
npm run dev
# Visit http://localhost:5173
```

### Run as a React Artifact (Claude.ai)

The `frontend/src/App.jsx` is also designed to run directly as a Claude React artifact — paste it into Claude.ai's artifact viewer and it will call the Anthropic API directly from the browser.

---

## 🔍 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/patrol/stream` | GET | Start patrol (Server-Sent Events stream) |
| `/api/frames` | GET | All indexed frames |
| `/api/alerts` | GET | All generated alerts |
| `/api/events` | GET | Event log |
| `/api/stats` | GET | Summary statistics |
| `/api/query/object/{name}` | GET | Frames by object type |
| `/api/query/location/{name}` | GET | Frames by zone |
| `/api/query/threat/{level}` | GET | Frames by threat level |
| `/api/ask` | POST | Answer follow-up questions |
| `/api/summary` | GET | Generate daily summary |

---

## 🧪 Test Cases

| Test | Expected |
|------|----------|
| All 15 frames indexed | ✅ |
| Blue Ford F150 logged ≥2 times | ✅ (3 occurrences) |
| Person loitering alert triggered | ✅ |
| Safety violation alert generated | ✅ |
| Vehicle repeat-visit alert triggered | ✅ |
| Query by object ("ford") returns results | ✅ |
| Query by location ("Main Gate") returns results | ✅ |
| Query by threat level ("high") returns results | ✅ |
| Query by time range returns results | ✅ |
| Export is JSON-serializable | ✅ |

---

## 🤖 AI Tool Usage

| Tool | What it did |
|------|-------------|
| **Claude (Anthropic API)** | Frame-by-frame security analysis, context-aware alert generation, daily summary, follow-up Q&A |
| **Claude Code** | Generated the initial FastAPI server skeleton, test scaffolding, and SSE streaming logic |
| **Claude.ai** | Validated architecture decisions, suggested the FrameIndex pattern, wrote the React dashboard |

Claude generated the core `analyze_frame_with_ai()` function with the JSON-structured prompt. I customized the threat level taxonomy and added the context window (last 5 events) to make alerts context-aware rather than stateless.

---

## 💡 Design Decisions

**Why simulated text frames instead of real video?**  
Simulated frames let us focus on the agent logic without requiring camera hardware. In production, frames would come from the drone's camera via OpenCV/RTSP, with a real VLM (BLIP-2, LLaVA, or GPT-4V) replacing the text descriptions.

**Why in-memory FrameIndex instead of a database?**  
For the prototype, in-memory keeps setup zero-dependency. The index interface (key-value with query methods) is designed to swap in ChromaDB, Pinecone, or SQLite without changing the agent logic.

**Why Claude over CLIP/BLIP?**  
Claude provides structured JSON output with reasoning out of the box. CLIP/BLIP are better for embedding-based similarity search at scale, but require more custom prompt engineering for the structured analysis this system needs. A production system would use BLIP-2 for visual features + Claude for reasoning.

**Context window management:**  
The agent passes the last 5 events as context to each analysis call. This enables cross-frame reasoning ("F150 second entry today") without blowing up token costs on a full history.

---

## 🚀 What Could Be Better (Given More Time)

1. **Real video input** — Replace text descriptions with actual OpenCV frame extraction + BLIP-2/LLaVA for visual understanding
2. **Vector database indexing** — Use ChromaDB for semantic search ("find frames similar to vehicle entry events")
3. **Push notifications** — WebSocket-based real-time alert push to mobile
4. **Multi-drone coordination** — Agent that reasons across multiple drone feeds simultaneously
5. **Anomaly detection** — Train a small model on "normal" patrol patterns to flag deviations
6. **Video summarization with timestamps** — Generate a 30-second highlight reel of the highest-threat moments

---

## 📁 Project Structure

```
drone-security-agent/
├── backend/
│   ├── agent.py        # Core AI agent logic
│   ├── server.py       # FastAPI REST + SSE server
│   └── tests.py        # 26-test test suite
├── frontend/
│   └── src/
│       └── App.jsx     # React dashboard
├── docs/
│   └── architecture.md # System design details
└── README.md
```
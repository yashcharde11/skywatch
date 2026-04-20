import { useState, useEffect, useRef, useCallback } from "react";

// ─── Agent Mentions ───────────────────────────────────────────────────────────
const AGENT_MENTIONS = [
  { tag: "telemetry", name: "Telemetry Analyst", desc: "Fuses telemetry & vision data" },
  { tag: "vision", name: "Vision Specialist", desc: "Extracts visual features & captions" },
  { tag: "data", name: "Drone Data Specialist", desc: "Raw sensor & telemetry data" },
  { tag: "security", name: "Drone Security Analyst", desc: "Security threats & events" },
  { tag: "code", name: "Coding Assistant", desc: "Software engineering assistant" },
  { tag: "reviewer", name: "Code Reviewer", desc: "Analyzes code for bugs/security" },
  { tag: "debug", name: "Debugging Expert", desc: "Finds & fixes errors" },
  { tag: "writer", name: "Technical Writer", desc: "Writes documentation" }
];

// ─── AI via Claude API ────────────────────────────────────────────────────────

async function askFollowUpQuestion(question, targetAgent = null) {
  const response = await fetch("http://127.0.0.1:8000/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: question,
      target_agent: targetAgent
    }),
  });
  const data = await response.json();
  return data.answer || "Unable to answer.";
}

// ─── Threat Colors ────────────────────────────────────────────────────────────

const threatColors = {
  low: { bg: "#0d2b0d", border: "#1a5c1a", text: "#4ade80", badge: "#166534" },
  medium: { bg: "#2b1f0d", border: "#6b4a0a", text: "#fbbf24", badge: "#92400e" },
  high: { bg: "#2b0d0d", border: "#6b1a1a", text: "#f87171", badge: "#991b1b" },
  critical: { bg: "#2b0020", border: "#8b005a", text: "#f472b6", badge: "#9d174d" },
};

const locationIcons = {
  "Main Gate": "🚪", "Parking Lot": "🅿️", "Garage": "🏠",
  "Perimeter": "🔒", "Rooftop": "🏗️", "Service Entrance": "📦",
  "Dock": "🛸", "default": "📍"
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function ThreatBadge({ level }) {
  const c = threatColors[level] || threatColors.low;
  return (
    <span style={{
      background: c.badge, color: c.text, border: `1px solid ${c.border}`,
      borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 700,
      letterSpacing: "0.08em", textTransform: "uppercase",
    }}>{level}</span>
  );
}

function PulsingDot({ color = "#4ade80" }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
      <span style={{
        width: 8, height: 8, borderRadius: "50%", background: color,
        boxShadow: `0 0 0 0 ${color}44`,
        animation: "pulse 1.5s infinite",
        display: "inline-block",
      }} />
    </span>
  );
}

function TelemetryBar({ label, value, max, unit, color = "#06b6d4" }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#94a3b8", marginBottom: 3 }}>
        <span>{label}</span>
        <span style={{ color: "#e2e8f0" }}>{value}{unit}</span>
      </div>
      <div style={{ height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 2, transition: "width 0.5s ease" }} />
      </div>
    </div>
  );
}

function DroneVisualizer({ frame, telemetry, isActive }) {
  const zones = [
    { id: "Main Gate", x: 50, y: 80, w: 80, h: 40 },
    { id: "Parking Lot", x: 160, y: 60, w: 90, h: 55 },
    { id: "Garage", x: 160, y: 130, w: 90, h: 40 },
    { id: "Perimeter", x: 10, y: 10, w: 330, h: 200, stroke: "#334155" },
    { id: "Rooftop", x: 270, y: 60, w: 70, h: 50 },
    { id: "Service Entrance", x: 270, y: 130, w: 70, h: 40 },
  ];
  const currentZone = frame?.location || telemetry?.zone || "Dock";
  const droneX = { "Main Gate": 90, "Parking Lot": 205, "Garage": 205, "Perimeter": 170, "Rooftop": 305, "Service Entrance": 305, "Dock": 170 }[currentZone] || 170;
  const droneY = { "Main Gate": 100, "Parking Lot": 88, "Garage": 150, "Perimeter": 105, "Rooftop": 85, "Service Entrance": 150, "Dock": 30 }[currentZone] || 105;

  return (
    <svg viewBox="0 0 350 220" style={{ width: "100%", height: "100%", background: "#0a1628" }}>
      {/* Grid */}
      {[...Array(7)].map((_, i) => (
        <line key={`v${i}`} x1={i * 50} y1={0} x2={i * 50} y2={220} stroke="#0d2035" strokeWidth={1} />
      ))}
      {[...Array(5)].map((_, i) => (
        <line key={`h${i}`} x1={0} y1={i * 55} x2={350} y2={i * 55} stroke="#0d2035" strokeWidth={1} />
      ))}
      {/* Zones */}
      {zones.map(z => (
        <g key={z.id}>
          <rect x={z.x} y={z.y} width={z.w} height={z.h}
            fill={currentZone === z.id ? "#0a2040" : "#060f1e"}
            stroke={currentZone === z.id ? "#06b6d4" : (z.stroke || "#1e3a5f")}
            strokeWidth={currentZone === z.id ? 1.5 : 1}
            rx={3} />
          <text x={z.x + z.w / 2} y={z.y + z.h / 2 + 4}
            textAnchor="middle" fill={currentZone === z.id ? "#7dd3fc" : "#334155"}
            fontSize={8} fontFamily="monospace">
            {z.id}
          </text>
        </g>
      ))}
      {/* Drone shadow */}
      <ellipse cx={droneX} cy={droneY + 15} rx={14} ry={4} fill="#000" opacity={0.3} />
      {/* Drone body */}
      <circle cx={droneX} cy={droneY} r={10} fill="#1e3a5f" stroke="#06b6d4" strokeWidth={1.5} />
      <circle cx={droneX} cy={droneY} r={4} fill="#06b6d4" />
      {/* Arms */}
      {[[-12, -12], [12, -12], [-12, 12], [12, 12]].map(([dx, dy], i) => (
        <g key={i}>
          <line x1={droneX} y1={droneY} x2={droneX + dx} y2={droneY + dy} stroke="#334155" strokeWidth={1.5} />
          <circle cx={droneX + dx} cy={droneY + dy} r={3} fill={isActive ? "#06b6d4" : "#334155"}
            style={isActive ? { animation: `spin ${0.3 + i * 0.05}s linear infinite` } : {}} />
        </g>
      ))}
      {/* Scan radius */}
      {isActive && (
        <circle cx={droneX} cy={droneY} r={30} fill="none" stroke="#06b6d444" strokeWidth={1}
          style={{ animation: "scanPulse 2s ease-out infinite" }} />
      )}
      {/* Label */}
      <text x={droneX} y={droneY - 18} textAnchor="middle" fill="#06b6d4" fontSize={9} fontFamily="monospace">
        DRONE-01
      </text>
    </svg>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function DroneSecurityDashboard() {
  const [status, setStatus] = useState("idle"); // idle | running | complete
  const [frames, setFrames] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [eventLog, setEventLog] = useState([]);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [currentTelemetry, setCurrentTelemetry] = useState({
    time: "00:00", lat: 37.7749, lon: -122.4194, altitude_m: 50, battery_pct: 100, speed_mps: 0.0, zone: "Dock"
  });
  const [progress, setProgress] = useState(0);
  const [dailySummary, setDailySummary] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [mentionFilter, setMentionFilter] = useState("");
  const [activeTab, setActiveTab] = useState("live");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [processingFrame, setProcessingFrame] = useState(false);
  const alertsEndRef = useRef(null);
  const chatInputRef = useRef(null);

  useEffect(() => {
    if (alertsEndRef.current) alertsEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [alerts]);

  const startPatrol = useCallback(() => {
    setStatus("running");
    setFrames([]);
    setAlerts([]);
    setEventLog([]);
    setDailySummary("");
    setProgress(0);
    setChatMessages([]);

    const source = new EventSource("http://127.0.0.1:8000/api/patrol/stream");

    source.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "start") {
        setProgress(0);
      } else if (data.type === "frame_start") {
        setCurrentFrame({ time: data.time, location: data.location, description: data.description });
        setProcessingFrame(true);
      } else if (data.type === "alert") {
        setAlerts(prev => [...prev, data.alert]);
      } else if (data.type === "frame_complete") {
        const { frame_id, analysis, telemetry } = data;
        setCurrentTelemetry(telemetry);

        const record = {
          frame_id, timestamp: telemetry.time, location: telemetry.zone,
          raw_description: analysis.summary || "",
          objects_detected: analysis.objects || [],
          event_type: analysis.event_type || "normal",
          threat_level: analysis.threat_level || "low",
          summary: analysis.summary || "",
          log_entry: analysis.log_entry || "",
        };

        setFrames(prev => [...prev, record]);
        setEventLog(prev => [...prev, {
          frame_id, time: telemetry.time, location: telemetry.zone,
          log: analysis.log_entry || "", threat_level: analysis.threat_level || "low",
        }]);

        setProgress(Math.round((frame_id / 15) * 100));
        setProcessingFrame(false);
      } else if (data.type === "complete") {
        setStatus("complete");
        setDailySummary(data.summary);
        source.close();
      }
    };

    source.onerror = (err) => {
      console.error("SSE Error:", err);
      setStatus("idle");
      setProcessingFrame(false);
      source.close();
    };
  }, []);

  const handleSearch = useCallback(() => {
    if (!searchQuery.trim()) return;
    const q = searchQuery.toLowerCase();
    const results = frames.filter(f =>
      f.objects_detected.some(o => o.toLowerCase().includes(q)) ||
      f.location.toLowerCase().includes(q) ||
      f.summary.toLowerCase().includes(q) ||
      f.threat_level.toLowerCase().includes(q)
    );
    setSearchResults({ query: searchQuery, results });
  }, [searchQuery, frames]);

  const handleChatInputChange = (e) => {
    const val = e.target.value;
    setChatInput(val);
    
    // Look for @ followed by word characters at the end of the input
    const match = val.match(/@(\w*)$/);
    if (match) {
      setShowSuggestions(true);
      setMentionFilter(match[1].toLowerCase());
    } else {
      setShowSuggestions(false);
    }
  };

  const handleSelectMention = (tag) => {
    const newVal = chatInput.replace(/@\w*$/, `@${tag} `);
    setChatInput(newVal);
    setShowSuggestions(false);
    chatInputRef.current?.focus();
  };

  const handleAskQuestion = useCallback(async () => {
    if (!chatInput.trim() || chatLoading) return;
    let question = chatInput.trim();
    let targetAgent = null;

    // Mapping of @mentions to internal agent names
    const agentMap = Object.fromEntries(AGENT_MENTIONS.map(a => [a.tag, a.name]));

    const match = question.match(/^@(\w+)/);
    if (match) {
      const tag = match[1].toLowerCase();
      if (agentMap[tag]) {
        targetAgent = agentMap[tag];
        // Strip the @tag from the question sent to the AI
        question = question.replace(/^@\w+\s*/, "");
      }
    }

    setChatInput("");
    setChatMessages(prev => [...prev, { role: "user", content: chatInput.trim() }]);
    setChatLoading(true);
    try {
      const answer = await askFollowUpQuestion(question, targetAgent);
      setChatMessages(prev => [...prev, { role: "assistant", content: answer }]);
    } catch (e) {
      setChatMessages(prev => [...prev, { role: "assistant", content: "Error processing your question. Please try again." }]);
    }
    setChatLoading(false);
  }, [chatInput, chatLoading, frames, alerts, eventLog]);

  const stats = {
    total: frames.length,
    high: frames.filter(f => f.threat_level === "high" || f.threat_level === "critical").length,
    alerts: alerts.length,
    battery: currentTelemetry.battery_pct,
  };

  // ─── Render ──────────────────────────────────────────────────────────────────

  return (
    <div style={{
      minHeight: "100vh", background: "#020b18", color: "#e2e8f0",
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
      padding: 0, margin: 0,
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Orbitron:wght@400;700;900&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #0a1628; }
        ::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 2px; }
        @keyframes pulse { 0%,100%{box-shadow:0 0 0 0 currentColor44} 50%{box-shadow:0 0 0 6px transparent} }
        @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        @keyframes scanPulse { 0%{r:20;opacity:0.8} 100%{r:60;opacity:0} }
        @keyframes slideIn { from{transform:translateX(20px);opacity:0} to{transform:translateX(0);opacity:1} }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
        .frame-card { animation: slideIn 0.3s ease; }
        .alert-card { animation: slideIn 0.3s ease; }
        .tab-btn { background: none; border: none; cursor: pointer; padding: "6px 16px"; font-family: inherit; font-size: 12; transition: all 0.2s; }
        .tab-btn:hover { color: #06b6d4; }
        input:focus { outline: none; }
        .mention-item { transition: background 0.2s; }
        .mention-item:hover { background: #0d2b4d; }
      `}</style>

      {/* Header */}
      <div style={{
        background: "linear-gradient(180deg, #0a1f3d 0%, #020b18 100%)",
        borderBottom: "1px solid #0d2b4d", padding: "12px 20px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ fontSize: 28 }}>🛸</div>
          <div>
            <div style={{
              fontFamily: "'Orbitron', monospace", fontSize: 16, fontWeight: 900,
              color: "#06b6d4", letterSpacing: "0.1em",
            }}>DRONE SECURITY ANALYST</div>
            <div style={{ fontSize: 10, color: "#475569", letterSpacing: "0.15em" }}>
              AUTONOMOUS SURVEILLANCE SYSTEM v1.0
            </div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {status === "running" && (
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "#06b6d4" }}>
              <PulsingDot color="#06b6d4" />
              PATROL ACTIVE — {progress}%
            </div>
          )}
          {status === "complete" && (
            <div style={{ fontSize: 11, color: "#4ade80" }}>✓ PATROL COMPLETE</div>
          )}
          <button
            onClick={startPatrol}
            disabled={status === "running"}
            style={{
              background: status === "running" ? "#0d2b4d" : "linear-gradient(135deg, #0369a1, #0284c7)",
              color: status === "running" ? "#475569" : "#fff",
              border: `1px solid ${status === "running" ? "#1e3a5f" : "#0284c7"}`,
              borderRadius: 6, padding: "8px 18px", fontSize: 12, fontWeight: 700,
              fontFamily: "inherit", cursor: status === "running" ? "not-allowed" : "pointer",
              letterSpacing: "0.08em",
            }}
          >
            {status === "running" ? "▶ PATROLLING..." : status === "complete" ? "↺ NEW PATROL" : "▶ START PATROL"}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      {status === "running" && (
        <div style={{ height: 2, background: "#0a1628" }}>
          <div style={{
            width: `${progress}%`, height: "100%",
            background: "linear-gradient(90deg, #0369a1, #06b6d4)",
            transition: "width 0.5s ease",
          }} />
        </div>
      )}

      {/* Stat Bar */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(4,1fr)",
        borderBottom: "1px solid #0d2b4d", background: "#040f22",
      }}>
        {[
          { label: "FRAMES ANALYZED", value: stats.total, icon: "🎬", color: "#06b6d4" },
          { label: "ALERTS GENERATED", value: stats.alerts, icon: "🚨", color: "#f87171" },
          { label: "HIGH THREAT EVENTS", value: stats.high, icon: "⚠️", color: "#fbbf24" },
          { label: "DRONE BATTERY", value: `${stats.battery}%`, icon: "🔋", color: "#4ade80" },
        ].map(s => (
          <div key={s.label} style={{
            padding: "10px 20px", borderRight: "1px solid #0d2b4d",
            display: "flex", alignItems: "center", gap: 10,
          }}>
            <span style={{ fontSize: 20 }}>{s.icon}</span>
            <div>
              <div style={{ fontSize: 18, fontWeight: 700, color: s.color, fontFamily: "'Orbitron',monospace" }}>
                {s.value}
              </div>
              <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.1em" }}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Main Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", height: "calc(100vh - 130px)", overflow: "hidden" }}>

        {/* Left Panel */}
        <div style={{ display: "flex", flexDirection: "column", overflow: "hidden", borderRight: "1px solid #0d2b4d" }}>

          {/* Tabs */}
          <div style={{
            display: "flex", borderBottom: "1px solid #0d2b4d",
            background: "#040f22", padding: "0 16px",
          }}>
            {["live", "frames", "search", "ask"].map(tab => (
              <button key={tab}
                onClick={() => setActiveTab(tab)}
                className="tab-btn"
                style={{
                  padding: "10px 16px", fontSize: 11, letterSpacing: "0.1em",
                  color: activeTab === tab ? "#06b6d4" : "#475569",
                  borderBottom: activeTab === tab ? "2px solid #06b6d4" : "2px solid transparent",
                  fontWeight: activeTab === tab ? 700 : 400,
                  fontFamily: "inherit", background: "none", border: "none",
                  borderBottom: activeTab === tab ? "2px solid #06b6d4" : "2px solid transparent",
                  cursor: "pointer",
                }}
              >
                {tab === "live" ? "🛸 LIVE VIEW" :
                  tab === "frames" ? "🎬 FRAME LOG" :
                    tab === "search" ? "🔍 SEARCH" : "💬 ASK AI"}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div style={{ flex: 1, overflow: "auto", padding: 16 }}>

            {/* LIVE VIEW */}
            {activeTab === "live" && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, height: "100%" }}>

                {/* Drone Map */}
                <div style={{
                  background: "#040f22", border: "1px solid #0d2b4d", borderRadius: 8,
                  overflow: "hidden", display: "flex", flexDirection: "column",
                }}>
                  <div style={{
                    padding: "8px 12px", borderBottom: "1px solid #0d2b4d",
                    fontSize: 10, color: "#475569", letterSpacing: "0.1em",
                  }}>
                    PATROL MAP — {currentTelemetry.zone}
                  </div>
                  <div style={{ flex: 1 }}>
                    <DroneVisualizer frame={currentFrame} telemetry={currentTelemetry} isActive={status === "running"} />
                  </div>
                </div>

                {/* Current Frame */}
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <div style={{
                    background: "#040f22", border: "1px solid #0d2b4d", borderRadius: 8, padding: 14,
                    flex: 1,
                  }}>
                    <div style={{ fontSize: 10, color: "#475569", letterSpacing: "0.1em", marginBottom: 10 }}>
                      CURRENT FRAME
                    </div>
                    {currentFrame ? (
                      <div>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                          <span style={{ color: "#06b6d4", fontSize: 13, fontWeight: 700 }}>
                            {locationIcons[currentFrame.location] || "📍"} {currentFrame.location}
                          </span>
                          <span style={{ color: "#475569", fontSize: 11 }}>T+{currentFrame.time}</span>
                        </div>
                        <p style={{ color: "#94a3b8", fontSize: 12, lineHeight: 1.6, margin: "0 0 12px" }}>
                          {currentFrame.description}
                        </p>
                        {processingFrame && (
                          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "#06b6d4" }}>
                            <span style={{ animation: "blink 0.8s infinite" }}>⬡</span>
                            Analyzing with Claude AI...
                          </div>
                        )}
                        {frames.length > 0 && frames[frames.length - 1].frame_id > 0 && (
                          <div style={{ marginTop: 8 }}>
                            <ThreatBadge level={frames[frames.length - 1].threat_level} />
                            <p style={{ color: "#64748b", fontSize: 11, marginTop: 8, marginBottom: 0 }}>
                              {frames[frames.length - 1].summary}
                            </p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div style={{ color: "#1e3a5f", fontSize: 12, textAlign: "center", paddingTop: 40 }}>
                        Start patrol to begin monitoring
                      </div>
                    )}
                  </div>

                  {/* Telemetry */}
                  <div style={{
                    background: "#040f22", border: "1px solid #0d2b4d", borderRadius: 8, padding: 14,
                  }}>
                    <div style={{ fontSize: 10, color: "#475569", letterSpacing: "0.1em", marginBottom: 10 }}>
                      TELEMETRY
                    </div>
                    <TelemetryBar label="Battery" value={currentTelemetry.battery_pct} max={100} unit="%" color="#4ade80" />
                    <TelemetryBar label="Altitude" value={currentTelemetry.altitude_m} max={100} unit="m" color="#06b6d4" />
                    <TelemetryBar label="Speed" value={currentTelemetry.speed_mps} max={10} unit=" m/s" color="#a78bfa" />
                    <div style={{ fontSize: 10, color: "#475569", marginTop: 8 }}>
                      📍 {currentTelemetry.lat.toFixed(4)}, {currentTelemetry.lon.toFixed(4)}
                    </div>
                  </div>
                </div>

                {/* Daily Summary */}
                {(dailySummary || isGeneratingSummary) && (
                  <div style={{
                    gridColumn: "1 / -1",
                    background: "#040f22", border: "1px solid #1e3a5f", borderRadius: 8, padding: 14,
                    borderLeft: "3px solid #06b6d4",
                  }}>
                    <div style={{ fontSize: 10, color: "#06b6d4", letterSpacing: "0.1em", marginBottom: 6 }}>
                      📊 DAILY PATROL SUMMARY
                    </div>
                    <p style={{ color: "#e2e8f0", fontSize: 13, margin: 0, lineHeight: 1.6 }}>
                      {isGeneratingSummary ? (
                        <span style={{ color: "#475569", animation: "blink 0.8s infinite" }}>Generating summary...</span>
                      ) : dailySummary}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* FRAME LOG */}
            {activeTab === "frames" && (
              <div>
                {frames.length === 0 ? (
                  <div style={{ color: "#1e3a5f", textAlign: "center", paddingTop: 60, fontSize: 13 }}>
                    No frames processed yet. Start a patrol.
                  </div>
                ) : (
                  frames.map(f => {
                    const c = threatColors[f.threat_level] || threatColors.low;
                    return (
                      <div key={f.frame_id} className="frame-card" style={{
                        background: c.bg, border: `1px solid ${c.border}`,
                        borderRadius: 6, padding: "10px 14px", marginBottom: 8,
                        borderLeft: `3px solid ${c.border}`,
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                          <span style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8" }}>
                            #{f.frame_id} · {locationIcons[f.location] || "📍"} {f.location}
                          </span>
                          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                            <span style={{ fontSize: 10, color: "#475569" }}>T+{f.timestamp}</span>
                            <ThreatBadge level={f.threat_level} />
                          </div>
                        </div>
                        <p style={{ color: "#94a3b8", fontSize: 12, margin: "0 0 6px", lineHeight: 1.5 }}>
                          {f.summary || f.raw_description}
                        </p>
                        <div style={{ fontSize: 10, color: "#475569" }}>
                          Objects: {f.objects_detected.join(", ") || "none"}
                        </div>
                        {f.log_entry && (
                          <div style={{ fontSize: 11, color: c.text, marginTop: 6, fontStyle: "italic" }}>
                            📋 {f.log_entry}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* SEARCH */}
            {activeTab === "search" && (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 11, color: "#475569", marginBottom: 8 }}>
                    Search indexed frames by object, location, or threat level
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      onKeyDown={e => e.key === "Enter" && handleSearch()}
                      placeholder='e.g. "truck", "Main Gate", "high"...'
                      style={{
                        flex: 1, background: "#040f22", border: "1px solid #1e3a5f",
                        borderRadius: 6, padding: "8px 12px", color: "#e2e8f0",
                        fontSize: 12, fontFamily: "inherit",
                      }}
                    />
                    <button onClick={handleSearch} style={{
                      background: "#0369a1", color: "#fff", border: "1px solid #0284c7",
                      borderRadius: 6, padding: "8px 16px", fontSize: 12, cursor: "pointer",
                      fontFamily: "inherit", fontWeight: 700,
                    }}>SEARCH</button>
                  </div>
                  <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                    {["truck", "person", "Main Gate", "high", "critical", "vehicle"].map(tag => (
                      <button key={tag} onClick={() => { setSearchQuery(tag); setTimeout(handleSearch, 50); }} style={{
                        background: "#0a1628", border: "1px solid #1e3a5f", borderRadius: 4,
                        padding: "3px 8px", fontSize: 10, color: "#475569", cursor: "pointer",
                        fontFamily: "inherit",
                      }}>{tag}</button>
                    ))}
                  </div>
                </div>
                {searchResults && (
                  <div>
                    <div style={{ fontSize: 11, color: "#06b6d4", marginBottom: 10 }}>
                      Found {searchResults.results.length} result(s) for "{searchResults.query}"
                    </div>
                    {searchResults.results.length === 0 ? (
                      <div style={{ color: "#475569", fontSize: 12 }}>No matching frames found.</div>
                    ) : (
                      searchResults.results.map(f => {
                        const c = threatColors[f.threat_level] || threatColors.low;
                        return (
                          <div key={f.frame_id} style={{
                            background: c.bg, border: `1px solid ${c.border}`,
                            borderRadius: 6, padding: "10px 14px", marginBottom: 8,
                          }}>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                              <span style={{ fontSize: 11, color: "#94a3b8" }}>
                                Frame #{f.frame_id} · {f.location}
                              </span>
                              <ThreatBadge level={f.threat_level} />
                            </div>
                            <p style={{ color: "#94a3b8", fontSize: 12, margin: 0 }}>{f.summary}</p>
                            <div style={{ fontSize: 10, color: "#475569", marginTop: 4 }}>
                              Objects: {f.objects_detected.join(", ")}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ASK AI */}
            {activeTab === "ask" && (
              <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
                <div style={{ flex: 1, overflow: "auto", marginBottom: 12 }}>
                  {chatMessages.length === 0 ? (
                    <div style={{ paddingTop: 20 }}>
                      <div style={{ color: "#475569", fontSize: 12, marginBottom: 16 }}>
                        Ask follow-up questions about the patrol after it's complete.
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                        {[
                          "How many times did the blue Ford F150 appear?",
                          "Were there any safety violations?",
                          "What objects were detected at the main gate?",
                          "Summarize all high-threat events",
                        ].map(q => (
                          <button key={q} onClick={() => setChatInput(q)} style={{
                            background: "#040f22", border: "1px solid #1e3a5f", borderRadius: 6,
                            padding: "8px 12px", color: "#64748b", fontSize: 11, textAlign: "left",
                            cursor: "pointer", fontFamily: "inherit",
                          }}>💬 {q}</button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    chatMessages.map((m, i) => (
                      <div key={i} style={{
                        marginBottom: 12,
                        display: "flex", flexDirection: "column",
                        alignItems: m.role === "user" ? "flex-end" : "flex-start",
                      }}>
                        <div style={{
                          background: m.role === "user" ? "#0369a1" : "#040f22",
                          border: `1px solid ${m.role === "user" ? "#0284c7" : "#1e3a5f"}`,
                          borderRadius: 8, padding: "8px 12px", maxWidth: "85%",
                          fontSize: 12, lineHeight: 1.6, color: m.role === "user" ? "#fff" : "#94a3b8",
                      whiteSpace: "pre-wrap",
                      overflowX: "auto",
                        }}>
                          {m.content}
                        </div>
                      </div>
                    ))
                  )}
                  {chatLoading && (
                    <div style={{ color: "#475569", fontSize: 11, animation: "blink 0.8s infinite" }}>
                      ⬡ Claude is analyzing...
                    </div>
                  )}
                </div>
                <div style={{ display: "flex", gap: 8, position: "relative" }}>
                  {showSuggestions && (
                    <div style={{
                      position: "absolute", bottom: "100%", left: 0, marginBottom: 8,
                      background: "#040f22", border: "1px solid #1e3a5f", borderRadius: 8,
                      width: "100%", maxWidth: 300, boxShadow: "0 -4px 12px rgba(0,0,0,0.5)",
                      zIndex: 10, overflow: "hidden"
                    }}>
                      {AGENT_MENTIONS.filter(a => a.tag.includes(mentionFilter)).length === 0 ? (
                        <div style={{ padding: "8px 12px", color: "#475569", fontSize: 11 }}>No agents found.</div>
                      ) : (
                        AGENT_MENTIONS.filter(a => a.tag.includes(mentionFilter)).map(a => (
                          <div key={a.tag} onClick={() => handleSelectMention(a.tag)}
                               className="mention-item"
                               style={{ padding: "8px 12px", cursor: "pointer", borderBottom: "1px solid #0a1628", display: "flex", flexDirection: "column", gap: 2 }}>
                            <div style={{ color: "#06b6d4", fontSize: 12, fontWeight: 700 }}>@{a.tag}</div>
                            <div style={{ color: "#94a3b8", fontSize: 10 }}>{a.desc}</div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                  <input
                    ref={chatInputRef}
                    value={chatInput}
                    onChange={handleChatInputChange}
                    onKeyDown={e => {
                      if (e.key === "Enter") {
                        if (showSuggestions) {
                          e.preventDefault();
                          setShowSuggestions(false);
                        } else {
                          handleAskQuestion();
                        }
                      }
                    }}
                    placeholder="Ask about the patrol..."
                    disabled={frames.length === 0 || chatLoading}
                    style={{
                      flex: 1, background: "#040f22", border: "1px solid #1e3a5f",
                      borderRadius: 6, padding: "8px 12px", color: "#e2e8f0",
                      fontSize: 12, fontFamily: "inherit",
                      opacity: frames.length === 0 ? 0.5 : 1,
                    }}
                  />
                  <button
                    onClick={handleAskQuestion}
                    disabled={frames.length === 0 || chatLoading}
                    style={{
                      background: "#0369a1", color: "#fff", border: "1px solid #0284c7",
                      borderRadius: 6, padding: "8px 14px", fontSize: 12, cursor: "pointer",
                      fontFamily: "inherit", fontWeight: 700,
                      opacity: frames.length === 0 ? 0.5 : 1,
                    }}
                  >ASK</button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel — Alerts */}
        <div style={{ display: "flex", flexDirection: "column", background: "#040f22", overflow: "hidden" }}>
          <div style={{
            padding: "10px 16px", borderBottom: "1px solid #0d2b4d",
            display: "flex", alignItems: "center", justifyContent: "space-between",
          }}>
            <span style={{ fontSize: 10, color: "#475569", letterSpacing: "0.1em" }}>
              🚨 ALERT FEED
            </span>
            <span style={{
              background: alerts.length > 0 ? "#991b1b" : "#1e3a5f",
              color: alerts.length > 0 ? "#fca5a5" : "#475569",
              borderRadius: 10, padding: "1px 7px", fontSize: 10, fontWeight: 700,
            }}>{alerts.length}</span>
          </div>
          <div style={{ flex: 1, overflow: "auto", padding: 12 }}>
            {alerts.length === 0 ? (
              <div style={{ color: "#1e3a5f", fontSize: 11, textAlign: "center", paddingTop: 40 }}>
                No alerts yet
              </div>
            ) : (
              alerts.map((a, i) => {
                const c = threatColors[a.threat_level] || threatColors.medium;
                return (
                  <div key={i} className="alert-card" style={{
                    background: c.bg, border: `1px solid ${c.border}`,
                    borderRadius: 6, padding: "10px 12px", marginBottom: 8,
                    borderLeft: `3px solid ${c.text}`,
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <ThreatBadge level={a.threat_level} />
                      <span style={{ fontSize: 10, color: "#475569" }}>T+{a.time}</span>
                    </div>
                    <p style={{ color: c.text, fontSize: 12, margin: "0 0 4px", lineHeight: 1.5, fontWeight: 500 }}>
                      {a.message}
                    </p>
                    <div style={{ fontSize: 10, color: "#475569" }}>
                      📍 {a.location} · Frame #{a.frame_id}
                    </div>
                  </div>
                );
              })
            )}
            <div ref={alertsEndRef} />
          </div>

          {/* Event Log mini */}
          <div style={{ borderTop: "1px solid #0d2b4d", padding: "10px 16px 0" }}>
            <div style={{ fontSize: 10, color: "#475569", letterSpacing: "0.1em", marginBottom: 8 }}>
              📋 EVENT LOG
            </div>
            <div style={{ maxHeight: 180, overflow: "auto", paddingBottom: 8 }}>
              {eventLog.length === 0 ? (
                <div style={{ color: "#1e3a5f", fontSize: 10 }}>No events logged</div>
              ) : (
                [...eventLog].reverse().map((e, i) => (
                  <div key={i} style={{
                    fontSize: 10, color: "#475569", padding: "3px 0",
                    borderBottom: "1px solid #0a1628",
                  }}>
                    <span style={{ color: "#1e3a5f" }}>{e.time} </span>
                    {e.log}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
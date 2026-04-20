"""
Drone Security Analyst Agent
Core agent logic: processes telemetry + video frames, indexes events, generates alerts
"""

import json
import yaml
import sys
import os
from typing import TypedDict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import time
import random
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from mock_data import SIMULATED_FRAMES, TELEMETRY_DATA
from frame_index import FrameIndex
from services.state import FrameAnalysisState
from config import GROQ_API_KEY, sky_ai
from services.sub_agents.sec_analyst import agent as drone_security_analyst
from services.sub_agents.data_ops import agent as drone_data_specialist
from services.sub_agents.vision import agent as vision_specialist
from services.sub_agents.telemetry import agent as telemetry_analyst
from services.sub_agents.red_team import agent as red_team_agent

# Initialize the LangChain Chat model with Groq
llm = sky_ai

def load_prompts():
    prompts_path = os.path.join(os.path.dirname(__file__), "prompts.yaml")
    with open(prompts_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

PROMPTS = load_prompts()

DRONE_PROMPT_TEMPLATE = PROMPTS["analyze_frame_prompt"]

# ─── LangGraph State & Nodes ────────────────────────────────────────────────────

def analyze_frame_node(state: FrameAnalysisState) -> dict:
    """LangGraph Node to analyze a video frame and generate structured analysis."""
    frame = state["frame"]
    telemetry = state["telemetry"]
    context_history = state["context_history"]

    context_str = "\n".join([f"- [{c['time']}] {c['summary']}" for c in context_history[-5:]])
    if not context_str:
        context_str = "No prior events."
    
    prompt = DRONE_PROMPT_TEMPLATE.format(
        frame_time=frame['time'],
        frame_location=frame['location'],
        frame_description=frame['description'],
        telemetry_altitude=telemetry['altitude_m'],
        telemetry_battery=telemetry['battery_pct'],
        telemetry_zone=telemetry['zone'],
        context_str=context_str
    )

    msg = llm.invoke([HumanMessage(content=prompt)])
    raw = msg.content.strip()
    
    # Clean up any markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    
    try:
        result = json.loads(raw)
    except Exception:
        result = {
            "objects": ["unknown"],
            "event_type": "unknown",
            "threat_level": "low",
            "summary": "Failed to parse AI response.",
            "alert": None,
            "log_entry": ""
        }
        
    return {"analysis_result": result}

# Build the Frame Analyzer Graph
workflow = StateGraph(FrameAnalysisState)
workflow.add_node("analyze", analyze_frame_node)
workflow.add_edge(START, "analyze")
workflow.add_edge("analyze", END)
frame_analyzer_app = workflow.compile()

# ─── Agent Interfaces ───────────────────────────────────────────────────────────

def analyze_frame_with_ai(frame: dict, telemetry: dict, context_history: list) -> dict:
    """Entry point for the backend to run the LangGraph frame analyzer."""
    state = {
        "frame": frame,
        "telemetry": telemetry,
        "context_history": context_history,
        "analysis_result": None
    }
    result_state = frame_analyzer_app.invoke(state)
    return result_state["analysis_result"]


def generate_daily_summary(index: FrameIndex) -> str:
    """Generate a one-sentence video summary (bonus feature)."""
    stats = index.get_summary_stats()
    events = [f["summary"] for f in index.frames if f["summary"]]
    events_str = "\n".join(f"- {e}" for e in events)
    
    prompt = PROMPTS["generate_daily_summary"].format(
        events_str=events_str,
        total_frames=stats['total_frames'],
        total_alerts=stats['total_alerts']
    )

    msg = llm.invoke([HumanMessage(content=prompt)])
    return msg.content.strip()

# ─── Supervisor Agent ───────────────────────────────────────────────────────────

class SupervisorState(TypedDict):
    input_text: str
    index: Optional[FrameIndex]
    result: str
    next_agent: str
    target_agent: Optional[str]

# Agent nodes that call the sub-agents

def drone_security_analyst_supervisor_node(state: SupervisorState) -> dict:
    if not state["index"] or not state["index"].frames:
        return {"result": PROMPTS["no_patrol_data_msg"]}
    result = drone_security_analyst.run(state["input_text"], state["index"])
    return {"result": result}

def drone_data_specialist_supervisor_node(state: SupervisorState) -> dict:
    if not state["index"] or not state["index"].frames:
        return {"result": PROMPTS["no_patrol_data_msg"]}
    result = drone_data_specialist.run(state["input_text"], state["index"])
    return {"result": result}

def vision_specialist_supervisor_node(state: SupervisorState) -> dict:
    if not state["index"] or not state["index"].frames:
        return {"result": PROMPTS["no_patrol_data_msg"]}
    result = vision_specialist.run(state["input_text"], state["index"])
    return {"result": result}

def telemetry_analyst_supervisor_node(state: SupervisorState) -> dict:
    if not state["index"] or not state["index"].frames:
        return {"result": PROMPTS["no_patrol_data_msg"]}
    result = telemetry_analyst.run(state["input_text"], state["index"])
    return {"result": result}

def red_team_agent_supervisor_node(state: SupervisorState) -> dict:
    if not state["index"] or not state["index"].frames:
        return {"result": PROMPTS["no_patrol_data_msg"]}
    result = red_team_agent.run(state["input_text"], state["index"])
    return {"result": result}

def router_node(state: SupervisorState) -> dict:
    # If the user explicitly targeted an agent via @mention, skip the routing logic
    if state.get("target_agent"):
        return {"next_agent": state["target_agent"]}

    prompt = PROMPTS["routing_prompt"].format(input_text=state["input_text"])
    msg = llm.invoke([HumanMessage(content=prompt)])
    raw_response = msg.content.strip().replace('"', '')
    
    # Robustly map the LLM's response to the correct node
    valid_agents = ["Coding Assistant", "Code Reviewer", "Technical Writer", "Debugging Expert", "Drone Security Analyst", "Drone Data Specialist", "Vision Specialist", "Telemetry Analyst", "Red Team Agent", "General"]
    next_node = "General"  # Fallback
    for agent in valid_agents:
        if agent.lower() in raw_response.lower():
            next_node = agent
            break
            
    return {"next_agent": next_node}

# Build the supervisor graph
supervisor_workflow = StateGraph(SupervisorState)
supervisor_workflow.add_node("router", router_node)
supervisor_workflow.add_node("Drone Security Analyst", drone_security_analyst_supervisor_node)
supervisor_workflow.add_node("Drone Data Specialist", drone_data_specialist_supervisor_node)
supervisor_workflow.add_node("Vision Specialist", vision_specialist_supervisor_node)
supervisor_workflow.add_node("Telemetry Analyst", telemetry_analyst_supervisor_node)
supervisor_workflow.add_node("Red Team Agent", red_team_agent_supervisor_node)
supervisor_workflow.add_node("General", lambda state: {"result": PROMPTS["general_fallback_msg"]})

supervisor_workflow.add_edge(START, "router")
supervisor_workflow.add_conditional_edges("router", lambda s: s['next_agent'], {k: k for k in ["Coding Assistant", "Code Reviewer", "Technical Writer", "Debugging Expert", "Drone Security Analyst", "Drone Data Specialist", "Vision Specialist", "Telemetry Analyst", "Red Team Agent", "General"]})
for agent in ["Coding Assistant", "Code Reviewer", "Technical Writer", "Debugging Expert", "Drone Security Analyst", "Drone Data Specialist", "Vision Specialist", "Telemetry Analyst", "Red Team Agent", "General"]:
    supervisor_workflow.add_edge(agent, END)

supervisor_app = supervisor_workflow.compile()

def run_supervisor(input_text: str, index: Optional[FrameIndex] = None, target_agent: Optional[str] = None) -> str:
    """Entry point for the supervisor agent to route and answer questions."""
    state = {
        "input_text": input_text, 
        "index": index,
        "result": "",
        "next_agent": "General",
        "target_agent": target_agent
    }
    result_state = supervisor_app.invoke(state)
    return result_state.get("result", "Error: No result returned from agents.")


# ─── Main Pipeline ──────────────────────────────────────────────────────────────

def run_security_patrol() -> dict:
    """Run the full drone security patrol simulation."""
    print("\n" + "="*60)
    print("  DRONE SECURITY ANALYST AGENT - STARTING PATROL")
    print("="*60)
    
    index = FrameIndex()
    context_history = []
    
    # Map telemetry by time
    telemetry_map = {t["time"]: t for t in TELEMETRY_DATA}
    default_telemetry = TELEMETRY_DATA[0]
    
    for i, frame in enumerate(SIMULATED_FRAMES):
        print(f"\n[{frame['time']}] Processing Frame {i+1}/{len(SIMULATED_FRAMES)} — {frame['location']}")
        
        # Get matching telemetry (find closest)
        telemetry = telemetry_map.get(frame["time"], default_telemetry)
        
        # AI Analysis
        try:
            analysis = analyze_frame_with_ai(frame, telemetry, context_history)
        except Exception as e:
            print(f"  ⚠ AI analysis error: {e}")
            analysis = {
                "objects": ["unknown"],
                "event_type": "unknown",
                "threat_level": "low",
                "summary": frame["description"],
                "alert": None,
                "log_entry": f"Frame {i+1}: {frame['description']}"
            }
        
        # Index the frame
        record = index.index_frame(
            frame_id=i+1,
            timestamp=frame["time"],
            location=frame["location"],
            raw_description=frame["description"],
            ai_analysis=analysis
        )
        
        # Log event
        log_entry = {
            "frame_id": i+1,
            "time": frame["time"],
            "location": frame["location"],
            "log": analysis.get("log_entry", ""),
            "threat_level": analysis["threat_level"]
        }
        index.log_event(log_entry)
        print(f"  📋 LOG: {analysis.get('log_entry', '')}")
        
        # Handle alerts
        if analysis.get("alert"):
            alert = {
                "frame_id": i+1,
                "time": frame["time"],
                "location": frame["location"],
                "message": analysis["alert"],
                "threat_level": analysis["threat_level"],
                "objects": analysis["objects"]
            }
            index.add_alert(alert)
            print(f"  🚨 ALERT [{analysis['threat_level'].upper()}]: {analysis['alert']}")
        
        # Update context
        context_history.append({
            "time": frame["time"],
            "summary": analysis.get("summary", ""),
            "threat_level": analysis["threat_level"]
        })
        
        time.sleep(0.3)  # Small delay to avoid rate limits
    
    # Generate daily summary
    print("\n" + "="*60)
    print("  GENERATING DAILY SUMMARY...")
    summary = generate_daily_summary(index)
    print(f"\n📊 DAILY SUMMARY: {summary}")
    
    # Demo follow-up questions
    print("\n" + "="*60)
    print("  FOLLOW-UP QUESTION DEMO...")
    q1 = "How many times did the blue Ford F150 appear and what did it do?"
    a1 = run_supervisor(q1, index)
    print(f"\n❓ Q: {q1}")
    print(f"💬 A: {a1}")
    
    q2 = "Were there any safety violations during the patrol?"
    a2 = run_supervisor(q2, index)
    print(f"\n❓ Q: {q2}")
    print(f"💬 A: {a2}")
    
    # Final export
    result = index.export()
    result["daily_summary"] = summary
    result["followup_demo"] = [
        {"question": q1, "answer": a1},
        {"question": q2, "answer": a2}
    ]
    
    print("\n" + "="*60)
    stats = result["stats"]
    print(f"  PATROL COMPLETE")
    print(f"  Frames Analyzed : {stats['total_frames']}")
    print(f"  Alerts Generated: {stats['total_alerts']}")
    print(f"  High Threat     : {stats['high_threat_frames']}")
    print("="*60)
    
    return result


if __name__ == "__main__":
    result = run_security_patrol()
    
    # Save results
    with open("patrol_results.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n✅ Results saved to patrol_results.json")
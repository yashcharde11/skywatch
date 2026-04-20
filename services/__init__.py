"""Agents package"""

from .sub_agents.sec_analyst import agent as drone_security_analyst
from .sub_agents.vision import agent as vision_specialist
from .sub_agents.telemetry import agent as telemetry_analyst
from .sub_agents.red_team import agent as red_team_agent
"""Coding Assistant Sub-Agent"""
"""Debugging Expert Sub-Agent"""
import sys
import os
from langchain_core.messages import HumanMessage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from config import sky_ai

def _get_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def run(input_text: str) -> str:
    """Runs the coding assistant agent."""
    """Runs the debugging expert agent."""
    system_prompt = _get_prompt()
    prompt = system_prompt + "\n\nUser Input:\n" + input_text
    msg = sky_ai.invoke([HumanMessage(content=prompt)])
    return msg.content.strip()
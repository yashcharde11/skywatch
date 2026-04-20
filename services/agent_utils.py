import os
import sys
from langchain_core.messages import HumanMessage

# Ensure root path is accessible to prevent import errors
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import sky_ai

def run_llm(system_prompt: str, user_input: str, context_data: str = None) -> str:
    """Centralized execution for all sub-agents to keep code DRY."""
    
    if context_data:
        prompt = f"{system_prompt}\n\nUser Input:\nQUESTION: {user_input}\n\nPATROL DATA:\n{context_data}"
    else:
        prompt = f"{system_prompt}\n\nUser Input:\n{user_input}"
        
    msg = sky_ai.invoke([HumanMessage(content=prompt)])
    return msg.content.strip()
"""Debugging Expert Sub-Agent"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from prompts_loader import get_prompt
from services.agent_utils import run_llm




# load prompt
system_prompt = get_prompt(__file__)





def run(input_text: str) -> str:
    """Runs the debugging expert agent."""
    return run_llm(system_prompt, input_text)
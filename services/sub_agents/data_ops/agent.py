"""Drone Data Specialist Sub-Agent for answering questions about raw data."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from frame_index import FrameIndex
from prompts_loader import get_prompt
from services.agent_utils import run_llm




# load prompt
system_prompt = get_prompt(__file__)





def run(question: str, index: FrameIndex) -> str:
    """Answer follow-up questions about the patrol's raw data."""
    return run_llm(system_prompt, question, context_data=json.dumps(index.export(), indent=2))
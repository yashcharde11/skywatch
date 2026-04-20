import os
from pathlib import Path

# Base path to the agents directory
BASE_DIR = Path(__file__).resolve().parent
AGENTS_DIR = BASE_DIR / "services" / "sub_agents"

# Dynamically imports all prompts.txt files as raw strings (eager loading)
ALL_PROMPTS = {}

for prompt_file in AGENTS_DIR.rglob("prompts.txt"):
    agent_name = prompt_file.parent.name
    ALL_PROMPTS[agent_name] = prompt_file.read_text(encoding="utf-8")

def get_prompt(file_path: str) -> str:
    """
    Clean one-liner to get a prompt by file path.
    Usage: prompt = get_prompt(__file__)
    """
    agent_name = os.path.basename(os.path.dirname(file_path))
    if agent_name not in ALL_PROMPTS:
        raise ValueError(f"Prompt file not found for agent '{agent_name}'.")
    return ALL_PROMPTS[agent_name]
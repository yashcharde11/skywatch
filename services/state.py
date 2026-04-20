"""
LangGraph State Definitions
"""
from typing import Optional, TypedDict

class FrameAnalysisState(TypedDict):
    frame: dict
    telemetry: dict
    context_history: list
    analysis_result: Optional[dict]
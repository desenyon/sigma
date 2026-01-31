"""Sigma - Elite Financial Research Agent."""

__version__ = "2.0.2"
__author__ = "Sigma"

from sigma.core.agent import SigmaAgent
from sigma.core.config import LLMProvider, get_settings

__all__ = ["SigmaAgent", "LLMProvider", "get_settings"]

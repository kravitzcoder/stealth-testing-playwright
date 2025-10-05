"""Configuration management"""
import json
from pathlib import Path

def load_config(filename: str) -> dict:
    """Load configuration file"""
    config_path = Path(__file__).parent / filename
    with open(config_path, 'r') as f:
        return json.load(f)

__all__ = ['load_config']

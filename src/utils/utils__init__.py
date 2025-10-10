"""
Utils Module - Enhanced with BrowserForge
==========================================

Exports utility classes and managers for the testing framework.
"""

# Device Profile Loader (CSV profiles)
from .device_profile_loader import DeviceProfileLoader

# BrowserForge Manager (NEW!)
from .browserforge_manager import BrowserForgeManager

__all__ = [
    'DeviceProfileLoader',
    'BrowserForgeManager',
]

__version__ = '2.0.0'  # Updated with BrowserForge integration

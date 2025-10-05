"""
STEALTH BROWSER TESTING FRAMEWORK - Test Result Model
Data model for test results with complete attribute support

Authors: kravitzcoder & MiniMax Agent
Phase: 1 - Foundation & Workflows (FIXED)
"""
from datetime import datetime
from typing import Optional
import json


class TestResult:
    """Container for comprehensive test results"""
    
    def __init__(
        self,
        library: str,
        category: str,
        test_name: str,
        url: str,
        success: bool,
        detected_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        proxy_working: bool = False,
        is_mobile_ua: bool = False,
        error: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        execution_time: float = 0.0,
        additional_data: Optional[dict] = None
    ):
        self.library = library
        self.category = category
        self.test_name = test_name
        self.url = url
        self.success = success
        self.detected_ip = detected_ip
        self.user_agent = user_agent
        self.proxy_working = proxy_working
        self.is_mobile_ua = is_mobile_ua
        self.error = error
        self.screenshot_path = screenshot_path
        self.execution_time = execution_time
        self.additional_data = additional_data or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """Convert result to dictionary for JSON serialization"""
        return {
            "library": self.library,
            "category": self.category,
            "test_name": self.test_name,
            "url": self.url,
            "success": self.success,
            "detected_ip": self.detected_ip,
            "user_agent": self.user_agent,
            "proxy_working": self.proxy_working,
            "is_mobile_ua": self.is_mobile_ua,
            "error": self.error,
            "screenshot_path": self.screenshot_path,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
            "additional_data": self.additional_data
        }
    
    def to_json(self) -> str:
        """Convert result to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TestResult':
        """Create TestResult from dictionary"""
        return cls(
            library=data.get("library", "unknown"),
            category=data.get("category", "unknown"),
            test_name=data.get("test_name", "unknown"),
            url=data.get("url", ""),
            success=data.get("success", False),
            detected_ip=data.get("detected_ip"),
            user_agent=data.get("user_agent"),
            proxy_working=data.get("proxy_working", False),
            is_mobile_ua=data.get("is_mobile_ua", False),
            error=data.get("error"),
            screenshot_path=data.get("screenshot_path"),
            execution_time=data.get("execution_time", 0.0),
            additional_data=data.get("additional_data", {})
        )
    
    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"TestResult({self.library}/{self.test_name}: {status})"
    
    def __str__(self) -> str:
        return self.to_json()

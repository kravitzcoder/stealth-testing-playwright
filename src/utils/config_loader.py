# src/utils/config_loader.py

import os
import json
import logging
from pathlib import Path

def load_device_profile(device_name):
    """
    Loads a device profile JSON from the config directory.
    
    Args:
        device_name (str): The name of the device profile to load (e.g., 'iphone_x').

    Returns:
        dict: The loaded device profile, or None if an error occurs.
    """
    logger = logging.getLogger(__name__)
    config_path = Path(__file__).parent.parent / "config" / "devices" / f"{device_name}.json"
    
    logger.debug(f"Attempting to load device profile from: {config_path}")
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Device profile not found: {config_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding device profile JSON '{config_path}': {e}")
        return None

def get_proxy_config(proxy_arg):
    """
    Parses the proxy argument from the CLI or environment variables.

    Args:
        proxy_arg (str): The proxy argument (e.g., 'host:port', 'env:').

    Returns:
        dict: A dictionary formatted for Playwright's proxy settings, or None.
    """
    logger = logging.getLogger(__name__)
    
    if proxy_arg.lower() == 'env:':
        host = os.environ.get('PROXY_HOST')
        port = os.environ.get('PROXY_PORT')
        username = os.environ.get('PROXY_USERNAME')
        password = os.environ.get('PROXY_PASSWORD')
        
        if not host or not port:
            logger.error("Proxy environment variables PROXY_HOST and PROXY_PORT must be set.")
            return None
        
        server = f"http://{host}:{port}"
        proxy_dict = {"server": server}
        if username:
            proxy_dict["username"] = username
        if password:
            proxy_dict["password"] = password
        return proxy_dict

    # Direct parsing from argument
    try:
        # Format: user:pass@host:port
        if '@' in proxy_arg:
            creds, endpoint = proxy_arg.split('@')
            user, pw = creds.split(':')
            host, port = endpoint.split(':')
            return {
                "server": f"http://{host}:{port}",
                "username": user,
                "password": pw
            }
        # Format: host:port
        elif ':' in proxy_arg:
            host, port = proxy_arg.split(':')
            return {"server": f"http://{host}:{port}"}
        else:
            raise ValueError("Invalid proxy format. Expected 'host:port' or 'user:pass@host:port'.")
    except ValueError as e:
        logger.error(f"Failed to parse proxy argument: {e}")
        return None

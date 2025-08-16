import subprocess
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

def restart_comfyui() -> bool:
    """
    Restart the ComfyUI container.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Restarting ComfyUI container...")
        result = subprocess.run(
            ["docker", "restart", "comfyui"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("ComfyUI container restarted successfully")
            return True
        else:
            logger.error(f"Failed to restart ComfyUI: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout while restarting ComfyUI")
        return False
    except Exception as e:
        logger.error(f"Error restarting ComfyUI: {e}")
        return False

def start_comfyui() -> bool:
    """
    Start ComfyUI container if it doesn't exist.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Starting ComfyUI container...")
        result = subprocess.run([
            "docker", "run", "--name", "comfyui",
            "-p", "8188:8188",
            "-v", "/storage/comfyui:/comfyui",
            "--restart", "unless-stopped",
            "--gpus", "all",
            "comfyui:13.08.25"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info("ComfyUI container started successfully")
            return True
        elif "already in use" in result.stderr:
            logger.info("ComfyUI container already exists, attempting restart")
            return restart_comfyui()
        else:
            logger.error(f"Failed to start ComfyUI: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout while starting ComfyUI")
        return False
    except Exception as e:
        logger.error(f"Error starting ComfyUI: {e}")
        return False

def check_comfyui_status() -> Optional[str]:
    """
    Check ComfyUI container status.
    Returns 'running', 'stopped', 'not_found', or None on error.
    """
    try:
        result = subprocess.run([
            "docker", "ps", "-a", "--format", "{{.Names}}:{{.Status}}"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return None
            
        for line in result.stdout.strip().split('\n'):
            if line.startswith('comfyui:'):
                if 'Up' in line:
                    return 'running'
                else:
                    return 'stopped'
        
        return 'not_found'
        
    except Exception as e:
        logger.error(f"Error checking ComfyUI status: {e}")
        return None

def force_restart_comfyui() -> bool:
    """
    Force restart ComfyUI by stopping and starting it.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Force restarting ComfyUI...")
        
        # Stop container if running
        subprocess.run(["docker", "stop", "comfyui"], 
                      capture_output=True, timeout=10)
        
        # Remove container
        subprocess.run(["docker", "rm", "comfyui"], 
                      capture_output=True, timeout=10)
        
        # Wait a moment
        time.sleep(2)
        
        # Start fresh container
        return start_comfyui()
        
    except Exception as e:
        logger.error(f"Error in force restart: {e}")
        return False 
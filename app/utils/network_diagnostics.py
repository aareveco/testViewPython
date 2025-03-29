"""
Network diagnostic utilities for AppStream
"""

import logging
import socket
import subprocess
import platform
import threading
import time
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def get_local_ip() -> str:
    """
    Get the local IP address of this machine
    
    Returns:
        str: The local IP address
    """
    try:
        # Create a socket to determine the outgoing IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # This doesn't actually establish a connection
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Error getting local IP: {e}")
        return "127.0.0.1"  # Fallback to localhost

def check_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """
    Check if a port is open on a remote host
    
    Args:
        host (str): The host to check
        port (int): The port to check
        timeout (float): Timeout in seconds
        
    Returns:
        bool: True if the port is open, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.error(f"Error checking port {port} on {host}: {e}")
        return False

def ping_host(host: str, count: int = 4) -> Tuple[bool, float]:
    """
    Ping a host to check connectivity
    
    Args:
        host (str): The host to ping
        count (int): Number of pings to send
        
    Returns:
        Tuple[bool, float]: (Success, Average round-trip time in ms)
    """
    try:
        # Determine the ping command based on the OS
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, str(count), host]
        
        # Run the ping command
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Check if the ping was successful
        if result.returncode == 0:
            # Extract the average round-trip time
            output = result.stdout
            if "Average" in output:  # Windows
                avg_line = [line for line in output.split("\n") if "Average" in line][0]
                avg_time = float(avg_line.split("=")[1].strip().split()[0])
            elif "min/avg/max" in output:  # Unix
                stats_line = [line for line in output.split("\n") if "min/avg/max" in line][0]
                avg_time = float(stats_line.split("=")[1].split("/")[1])
            else:
                avg_time = 0.0
                
            return True, avg_time
        else:
            return False, 0.0
    except Exception as e:
        logger.error(f"Error pinging {host}: {e}")
        return False, 0.0

def run_network_diagnostics(host: str, ports: List[int]) -> Dict[str, Any]:
    """
    Run comprehensive network diagnostics
    
    Args:
        host (str): The host to diagnose
        ports (List[int]): The ports to check
        
    Returns:
        Dict[str, Any]: Diagnostic results
    """
    results = {
        "host": host,
        "local_ip": get_local_ip(),
        "ping": None,
        "ports": {},
        "firewall_issues": False,
        "recommendations": []
    }
    
    # Check if we can ping the host
    ping_success, ping_time = ping_host(host)
    results["ping"] = {
        "success": ping_success,
        "time_ms": ping_time
    }
    
    if not ping_success:
        results["recommendations"].append(
            "Cannot ping the host. Check that both computers are on the same network."
        )
        results["firewall_issues"] = True
    
    # Check each port
    for port in ports:
        port_open = check_port_open(host, port)
        results["ports"][port] = port_open
        
        if not port_open:
            results["recommendations"].append(
                f"Port {port} is closed. Check your firewall settings and make sure this port is allowed."
            )
            results["firewall_issues"] = True
    
    # Add general recommendations
    if results["firewall_issues"]:
        results["recommendations"].append(
            "Consider temporarily disabling your firewall for testing, or add an exception for the AppStream application."
        )
        results["recommendations"].append(
            "If you're on a corporate or school network, try using ngrok for tunneling through firewalls."
        )
    
    return results

class ConnectionTester:
    """Class for testing network connections in the background"""
    
    def __init__(self, host: str, ports: List[int], callback: callable):
        """
        Initialize the connection tester
        
        Args:
            host (str): The host to test
            ports (List[int]): The ports to test
            callback (callable): Function to call with results
        """
        self.host = host
        self.ports = ports
        self.callback = callback
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the connection testing thread"""
        if self.thread and self.thread.is_alive():
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_tests)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the connection testing thread"""
        self.running = False
        if self.thread:
            self.thread.join(1.0)
    
    def _run_tests(self):
        """Run the connection tests"""
        try:
            # Initial diagnostics
            results = run_network_diagnostics(self.host, self.ports)
            self.callback(results)
            
            # Continuous port monitoring
            while self.running:
                port_status = {}
                for port in self.ports:
                    port_status[port] = check_port_open(self.host, port)
                
                self.callback({"ports": port_status})
                time.sleep(2.0)  # Check every 2 seconds
        except Exception as e:
            logger.error(f"Error in connection tester: {e}")
            self.callback({"error": str(e)})
        finally:
            self.running = False

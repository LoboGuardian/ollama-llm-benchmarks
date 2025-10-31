# resource_monitor.py
import psutil
import subprocess
import re
import os
import time

class ResourceMonitor:
    """
    Monitors CPU, RAM, and Temperature for the host system and the Ollama process.
    """
    def __init__(self, ollama_pid: int = None):
        self.ollama_pid = self._find_ollama_pid()
        self.ollama_process = psutil.Process(self.ollama_pid) if self.ollama_pid else None

    def _find_ollama_pid(self) -> int | None:
        """
        Attempts to find the PID of the running 'ollama' process.
        """
        # Iterate over all running processes to find the Ollama server
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            # Check for the main 'ollama' command
            if 'ollama' in proc.info['name'].lower() or \
               (proc.info['cmdline'] and 'ollama' in ' '.join(proc.info['cmdline']).lower()):
                # Exclude this script itself if it was run via an 'ollama' command alias
                if proc.pid != os.getpid():
                    print(f"Found Ollama process with PID: {proc.pid}")
                    return proc.pid
        print("Warning: Could not find the Ollama process PID. Monitoring system-wide resources only.")
        return None

    def _get_system_temperature(self) -> float | None:
        """
        Retrieves CPU temperature (Linux-specific using `sensors`).
        Requires `lm-sensors` to be installed on the host.
        Prioritizes common CPU/Package/Core temperatures.
        """
        try:
            # Use subprocess.run for robust command execution
            result = subprocess.run(['sensors'], capture_output=True, text=True, check=True, timeout=5)
            output = result.stdout
            
            # Keywords to prioritize for system/CPU temperature extraction
            # Based on common output (Package, Core) and your specific output (cpu_thermal, temp1 under an ADC)
            keywords = ['Package id 0', 'Core 0', 'cpu_thermal', 'temp1']
            
            # Use a pattern to find any temperature line and extract the first float value
            # Pattern: matches a '+' followed by digits, a dot, and digits, then '°C'
            temp_pattern = re.compile(r'\+(\d+\.\d+)°C')
            
            # Simple, direct parsing for a temperature value
            for line in output.split('\n'):
                line_lower = line.strip().lower()

                # Check for the specific CPU-related identifiers first
                if any(k.lower() in line_lower for k in keywords):
                    match = temp_pattern.search(line)
                    if match:
                        return float(match.group(1))

            # Fallback: If no specific keyword is found, search for the highest temperature
            # This is more robust for unusual sensor names (like 'rp1_adc-isa-c8000')
            highest_temp = None
            for line in output.split('\n'):
                match = temp_pattern.search(line)
                if match:
                    temp = float(match.group(1))
                    if highest_temp is None or temp > highest_temp:
                        highest_temp = temp

            return highest_temp

        except (FileNotFoundError, subprocess.CalledProcessError, IndexError, ValueError) as e:
            # Log or handle the error appropriately
            print(f"Error during temperature retrieval: {e}")
            return None

    def get_resource_snapshot(self) -> dict:
        """
        Captures a single snapshot of system and Ollama process resources.
        """
        # System-wide metrics
        system_cpu = psutil.cpu_percent(interval=None) # Non-blocking call
        system_memory = psutil.virtual_memory()

        data = {
            "timestamp": time.time(),
            "system_cpu_percent": system_cpu,
            "system_ram_used_gb": round(system_memory.used / (1024*2), 2),
            "system_temp_celsius": self._get_system_temperature()
        }

        # Ollama process-specific metrics
        if self.ollama_process:
            try:
                process_cpu = self.ollama_process.cpu_percent(interval=None)
                process_memory = self.ollama_process.memory_info()
                
                data["ollama_process_cpu_percent"] = process_cpu
                data["ollama_process_ram_rss_gb"] = round(process_memory.rss / (1024**3), 2)
            except psutil.NoSuchProcess:
                data["ollama_process_status"] = "Process not found (Crashed/Exited)"
                self.ollama_process = None # Reset the process handle
        
        return data
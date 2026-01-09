#!/usr/bin/env python3
"""
Kill processes using port 8003 and start the backend
"""
import subprocess
import sys
import time

def kill_port_8003():
    """Kill any processes using port 8003"""
    try:
        # Find processes using port 8003
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        pids_to_kill = []
        for line in lines:
            if ':8003' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    pids_to_kill.append(pid)
        
        # Kill each process
        for pid in set(pids_to_kill):  # Remove duplicates
            try:
                subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
                print(f"✅ Killed process {pid} using port 8003")
            except:
                print(f"⚠️ Could not kill process {pid}")
        
        if pids_to_kill:
            time.sleep(2)  # Wait for processes to terminate
        return True
        
    except Exception as e:
        print(f"❌ Error killing processes: {e}")
        return False

def start_backend():
    """Start the backend server"""
    try:
        print("🚀 Starting backend server...")
        subprocess.run([sys.executable, 'run.py'])
    except KeyboardInterrupt:
        print("\n👋 Backend stopped by user")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

if __name__ == "__main__":
    print("🔧 Fixing port 8003 issues...")
    kill_port_8003()
    start_backend()

"""
Helper script to check if a port is in use and optionally kill the process.
Useful for resolving "port already in use" errors.
"""
import socket
import sys
import subprocess
import platform


def is_port_in_use(port: int) -> bool:
    """Check if a port is currently in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except OSError:
            return True


def find_process_using_port(port: int):
    """Find the process ID using the specified port."""
    system = platform.system()
    
    if system == "Windows":
        try:
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        return parts[-1]
        except Exception as e:
            print(f"Error finding process: {e}")
    else:
        try:
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True
            )
            pid = result.stdout.strip()
            if pid:
                return pid
        except Exception as e:
            print(f"Error finding process: {e}")
    
    return None


def kill_process(pid: str):
    """Kill a process by PID."""
    system = platform.system()
    
    if system == "Windows":
        try:
            subprocess.run(['taskkill', '/PID', pid, '/F'], check=True)
            print(f"✅ Process {pid} terminated successfully")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Failed to kill process {pid}")
            return False
    else:
        try:
            subprocess.run(['kill', '-9', pid], check=True)
            print(f"✅ Process {pid} terminated successfully")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Failed to kill process {pid}")
            return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python check_port.py <port> [--kill]")
        print("Example: python check_port.py 8000")
        print("Example: python check_port.py 8000 --kill")
        sys.exit(1)
    
    try:
        port = int(sys.argv[1])
    except ValueError:
        print(f"❌ Invalid port number: {sys.argv[1]}")
        sys.exit(1)
    
    kill_flag = '--kill' in sys.argv
    
    print(f"Checking port {port}...")
    
    if is_port_in_use(port):
        print(f"⚠️  Port {port} is currently in use")
        pid = find_process_using_port(port)
        
        if pid:
            print(f"📌 Process ID using port {port}: {pid}")
            
            if kill_flag:
                print(f"Attempting to kill process {pid}...")
                if kill_process(pid):
                    print(f"✅ Port {port} should now be available")
                else:
                    print(f"❌ Could not kill process. You may need to run as administrator.")
            else:
                print(f"\n💡 To kill this process, run:")
                if platform.system() == "Windows":
                    print(f"   python check_port.py {port} --kill")
                    print(f"   Or manually: taskkill /PID {pid} /F")
                else:
                    print(f"   python check_port.py {port} --kill")
                    print(f"   Or manually: kill -9 {pid}")
        else:
            print(f"⚠️  Could not find process using port {port}")
            print(f"   You may need to check manually or restart your computer")
    else:
        print(f"✅ Port {port} is available")


if __name__ == "__main__":
    main()


import socket
import subprocess
import sys
import os
import signal
import time
import threading
from pathlib import Path
import tempfile
import json


class NetworkService:
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port
        self.socket = None
        self.process = None
        self.running = False
        
    def find_available_port(self, start_port=8080, max_attempts=100):
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    return port
            except OSError:
                continue
        raise RuntimeError("No available ports found")
    
    def start_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if os.name != 'nt':
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"Server started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    self.socket.settimeout(1.0)
                    client_socket, addr = self.socket.accept()
                    
                    thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, addr)
                    )
                    thread.daemon = True
                    thread.start()
                    
                except socket.timeout:
                    continue
                except OSError:
                    if self.running:
                        print("Socket error occurred")
                    break
                    
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop_server()
    
    def handle_client(self, client_socket, addr):
        try:
            data = client_socket.recv(1024).decode('utf-8')
            response = f"Echo: {data}"
            client_socket.send(response.encode('utf-8'))
        except Exception as e:
            print(f"Client handling error: {e}")
        finally:
            client_socket.close()
    
    def stop_server(self):
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None


class ProcessManager:
    def __init__(self):
        self.processes = {}
        self.pid_file = self._get_pid_file_path()
    
    def _get_pid_file_path(self):
        if os.name == 'nt':
            temp_dir = tempfile.gettempdir()
        else:
            temp_dir = "/var/run" if os.path.exists("/var/run") else tempfile.gettempdir()
        
        return Path(temp_dir) / "network_service.pid"
    
    def start_background_process(self, command, process_name):
        try:
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
                process = subprocess.Popen(
                    command,
                    creationflags=creationflags,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                process = subprocess.Popen(
                    command,
                    preexec_fn=os.setsid,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            self.processes[process_name] = process
            self._save_pid_info()
            
            return process.pid
            
        except Exception as e:
            print(f"Failed to start process {process_name}: {e}")
            return None
    
    def stop_process(self, process_name):
        if process_name not in self.processes:
            return False
        
        process = self.processes[process_name]
        
        try:
            if os.name == 'nt':
                process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name == 'nt':
                    process.kill()
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait()
            
            del self.processes[process_name]
            self._save_pid_info()
            return True
            
        except Exception as e:
            print(f"Error stopping process {process_name}: {e}")
            return False
    
    def _save_pid_info(self):
        try:
            pid_info = {
                name: proc.pid for name, proc in self.processes.items()
                if proc.poll() is None
            }
            
            with open(self.pid_file, 'w') as f:
                json.dump(pid_info, f)
                
        except Exception as e:
            print(f"Failed to save PID info: {e}")
    
    def cleanup_processes(self):
        for name in list(self.processes.keys()):
            self.stop_process(name)
        
        if self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except OSError:
                pass


def setup_signal_handlers():
    def signal_handler(signum, frame):
        print("Received termination signal, cleaning up...")
        pm = ProcessManager()
        pm.cleanup_processes()
        sys.exit(0)
    
    if os.name != 'nt':
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    else:
        signal.signal(signal.SIGINT, signal_handler)


def get_network_interfaces():
    interfaces = []
    
    try:
        hostname = socket.gethostname()
        interfaces.append(("hostname", hostname))
        
        local_ip = socket.gethostbyname(hostname)
        interfaces.append(("local_ip", local_ip))
        
    except Exception as e:
        print(f"Failed to get network info: {e}")
    
    return interfaces


if __name__ == "__main__":
    setup_signal_handlers()
    
    service = NetworkService()
    available_port = service.find_available_port()
    service.port = available_port
    
    pm = ProcessManager()
    
    interfaces = get_network_interfaces()
    print(f"Network interfaces: {interfaces}")
    
    server_thread = threading.Thread(target=service.start_server)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        time.sleep(2)
        
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.connect(("localhost", available_port))
        test_socket.send(b"Hello, server!")
        response = test_socket.recv(1024)
        print(f"Server response: {response.decode('utf-8')}")
        test_socket.close()
        
    except Exception as e:
        print(f"Test connection failed: {e}")
    
    finally:
        service.stop_server()
        pm.cleanup_processes()
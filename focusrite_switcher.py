import sys
import os
import socket
import time
import win32gui
import win32con

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
HOST = "127.0.0.1"
PORT_START = 49152
PORT_END = 50000  # Captures your active port 49673
TIMEOUT = 0.02

APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
LOG_FILE_PATH = os.path.join(APP_DIR, "error.log")

# ==============================================================================
# ROUTING COMMAND ARRAYS (Direct TCP Strings)
# ==============================================================================
# Mode 1: PLAYBACK ONLY (Routes computer audio only, mutes physical hardware inputs)
PLAYBACK_ONLY_COMMANDS = [
    '<client_command type="assign_source" output="line_output_1" source="daw_output_1"/>',
    '<client_command type="assign_source" output="line_output_2" source="daw_output_2"/>'
]

# Mode 2: STANDALONE (Routes physical hardware inputs directly to your main speakers)
STANDALONE_COMMANDS = [
    '<client_command type="assign_source" output="line_output_1" source="analogue_input_1"/>',
    '<client_command type="assign_source" output="line_output_2" source="analogue_input_2"/>'
]

FLASH_HARDWARE_COMMAND = '<client_command type="flash_hardware"/>'
# ==============================================================================

def log_error_and_exit(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] ERROR: {message}\n"
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(formatted_msg)
    except Exception:
        pass
    win32gui.MessageBox(0, message, "Focusrite Switcher Error", win32con.MB_ICONERROR | win32con.MB_OK)
    sys.exit(1)


def find_active_server_port():
    print(f"Scanning local TCP ports {PORT_START}-{PORT_END}...")
    for port in range(PORT_START, PORT_END + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(TIMEOUT)
                if s.connect_ex((HOST, port)) == 0:
                    print(f" -> Found Focusrite Control Server on TCP port {port}")
                    return port
        except Exception:
            continue
    return None


def execute_tcp_stream(port, command_list, should_flash=False):
    """Establishes a single socket context and fires sequentially bounded string packages."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)
            s.connect((HOST, port))
            
            for cmd in command_list:
                # Generate strict length-prefix packet framing with trailing delimiter
                payload = f"Length={len(cmd):06d} {cmd}\n"
                print(f"Sending Matrix Payload: {cmd}")
                s.sendall(payload.encode('utf-8'))
                time.sleep(0.05) # Brief gap to prevent packet collisions
                
            if should_flash:
                flash_payload = f"Length={len(FLASH_HARDWARE_COMMAND):06d} {FLASH_HARDWARE_COMMAND}\n"
                print("Sending non-volatile hardware save flash...")
                s.sendall(flash_payload.encode('utf-8'))
                time.sleep(0.1)
                
    except Exception as e:
        log_error_and_exit(f"Failed to transmit data to server on port {port}. Error: {str(e)}")


def execute_routing(mode):
    port = find_active_server_port()
    if not port:
        log_error_and_exit("Could not detect an active Focusrite Control Server instance.")

    if mode == "playback_only":
        print("Switching matrix to Playback Only configuration...")
        execute_tcp_stream(port, PLAYBACK_ONLY_COMMANDS, should_flash=False)
        
    elif mode == "standalone":
        print("Switching matrix to Standalone Hardware routing...")
        execute_tcp_stream(port, STANDALONE_COMMANDS, should_flash=True)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ["playback_only", "standalone"]:
        log_error_and_exit("Invalid or missing execution argument structure.")
        
    try:
        execute_routing(sys.argv[1])
    except Exception as e:
        log_error_and_exit(f"An unexpected runtime exception occurred:\n{str(e)}")
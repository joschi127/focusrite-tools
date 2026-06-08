import sys
import os
import socket
import time
import yaml
try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# ==============================================================================
# CONFIGURATION DEFAULTS
# ==============================================================================
DEFAULT_CONFIG = {
    "network": {
        "host": "127.0.0.1",
        "port_range": [49152, 50000],
        "timeout": 0.02
    },
    "routing": {
        "playback_only": [
            '<client_command type="assign_source" output="line_output_1" source="daw_output_1"/>',
            '<client_command type="assign_source" output="line_output_2" source="daw_output_2"/>'
        ],
        "standalone": [
            '<client_command type="assign_source" output="line_output_1" source="analogue_input_1"/>',
            '<client_command type="assign_source" output="line_output_2" source="analogue_input_2"/>'
        ],
        "flash_command": '<client_command type="flash_hardware"/>'
    }
}

APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CONFIG_FILE_PATH = os.path.join(APP_DIR, "config.yml")
LOG_FILE_PATH = os.path.join(APP_DIR, "error.log")

def load_config():
    """Loads config from YAML, merges with defaults, and saves if changes were made."""
    config = DEFAULT_CONFIG.copy()
    updated = False

    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                loaded_config = yaml.safe_load(f) or {}
            
            # Deep merge logic for the two-level dictionary
            for section, values in DEFAULT_CONFIG.items():
                if section not in loaded_config:
                    loaded_config[section] = values
                    updated = True
                else:
                    for key, val in values.items():
                        if key not in loaded_config[section]:
                            loaded_config[section][key] = val
                            updated = True
            config = loaded_config
        except Exception as e:
            # If config is corrupted, we'll log it but proceed with defaults
            # (In a real app, maybe we'd want to notify the user)
            pass
    else:
        updated = True

    if updated:
        try:
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        except Exception:
            pass
    
    return config

# Load active configuration
CONFIG = load_config()

# Helper accessors for clarity
HOST = CONFIG["network"]["host"]
PORT_START, PORT_END = CONFIG["network"]["port_range"]
TIMEOUT = CONFIG["network"]["timeout"]

PLAYBACK_ONLY_COMMANDS = CONFIG["routing"]["playback_only"]
STANDALONE_COMMANDS = CONFIG["routing"]["standalone"]
FLASH_HARDWARE_COMMAND = CONFIG["routing"]["flash_command"]
# ==============================================================================

def log_error_and_exit(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] ERROR: {message}\n"
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(formatted_msg)
    except Exception:
        pass
    if HAS_WIN32:
        win32gui.MessageBox(0, message, "Focusrite Switcher Error", win32con.MB_ICONERROR | win32con.MB_OK)
    else:
        print(f"UI NOTIFICATION (Simulated): {message}")
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
    mode = "playback_only"
    if len(sys.argv) >= 2:
        if sys.argv[1] in ["playback_only", "standalone"]:
            mode = sys.argv[1]
        else:
            log_error_and_exit(f"Invalid execution argument: {sys.argv[1]}")
        
    try:
        execute_routing(mode)
    except Exception as e:
        log_error_and_exit(f"An unexpected runtime exception occurred:\n{str(e)}")

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

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(APP_DIR, "config.yml")
DEFAULT_CONFIG_FILE_PATH = os.path.join(APP_DIR, "config.default.yml")
LOG_FILE_PATH = os.path.join(APP_DIR, "error.log")

def save_config(config):
    """Saves the current configuration to the YAML file."""
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except Exception:
        pass

def load_yaml(file_path):
    """Loads a YAML file and returns its content as a dictionary."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}

def load_config():
    """Loads config from YAML and merges with defaults from config.default.yml."""
    default_config = load_yaml(DEFAULT_CONFIG_FILE_PATH)
    loaded_config = load_yaml(CONFIG_FILE_PATH)
    
    config = {}

    # Deep merge and handle '~' (None)
    for section, values in default_config.items():
        if section not in config:
            config[section] = {}
        loaded_section = loaded_config.get(section, {})
        
        for key, default_val in values.items():
            loaded_val = loaded_section.get(key)
            # If key is missing or explicitly set to None (~)
            if key not in loaded_section or loaded_val is None:
                config[section][key] = default_val
            else:
                config[section][key] = loaded_val

    # Ensure any extra top-level sections or keys in config.yml are preserved
    for section, values in loaded_config.items():
        if section not in config:
            config[section] = values
        elif isinstance(values, dict):
            for key, val in values.items():
                if key not in config[section]:
                    config[section][key] = val
        elif section in config and not isinstance(config[section], dict):
             # If it's a top level key that's not a dict, it's already handled or should be preserved
             pass
    
    # Ensure mandatory sections exist in config to avoid KeyError during initialization
    for section in ["network", "profiles"]:
        if section not in config:
            config[section] = default_config.get(section, {})
    
    return config, loaded_config

# Load active configuration
CONFIG, LOADED_CONFIG = load_config()

# Helper accessors for clarity
HOST = CONFIG["network"]["host"]
PORT_START, PORT_END = CONFIG["network"]["port_range"]
TIMEOUT = CONFIG["network"]["timeout"]

def show_warning(message):
    """Logs a warning to the console and shows a message box if on Windows."""
    print(f"WARNING: {message}")
    if HAS_WIN32:
        win32gui.MessageBox(0, message, "Focusrite Switcher Warning", win32con.MB_ICONWARNING | win32con.MB_OK)


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
    last_port = CONFIG["network"].get("last_successful_port")
    if last_port:
        print(f"Trying last successful port: {last_port}...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(TIMEOUT)
                if s.connect_ex((HOST, last_port)) == 0:
                    print(f" -> Found Focusrite Control Server on last saved successful port {last_port}")
                    return last_port
        except Exception:
            pass

    print(f"Scanning local TCP ports {PORT_START}-{PORT_END}...")
    for port in range(PORT_START, PORT_END + 1):
        if port == last_port:
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(TIMEOUT)
                if s.connect_ex((HOST, port)) == 0:
                    print(f" -> Found Focusrite Control Server on TCP port {port}")
                    return port
        except Exception:
            continue
    return None


def execute_tcp_stream(port, command_list):
    """Establishes a single socket context and fires sequentially bounded string packages."""
    handshake = '<client-details hostname="focusrite-tools" client-name="FocusriteSwitcher" client-id="123456"/>'
    payload_handshake = f"Length={len(handshake):06d} {handshake}\n"

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((HOST, port))
            
            # 1. Send Handshake and Initial Command(s)
            s.sendall(payload_handshake.encode('utf-8'))
            
            # We don't wait for handshake response separately as some servers
            # only send the full state dump after the first real command.
            
            # 2. Send actual commands
            s.setblocking(True)
            for cmd in command_list:
                if not cmd:
                    continue

                # Generate strict length-prefix packet framing with trailing delimiter
                payload = f"Length={len(cmd):06d} {cmd}\n"
                print(f"Sending Matrix Payload: {cmd}")
                s.sendall(payload.encode('utf-8'))
                
                # 3. Await acknowledgment for each command (including the state dump)
                cmd_response = b""
                cmd_start_time = time.time()
                while time.time() - cmd_start_time < 2.0:
                    try:
                        s.setblocking(False)
                        chunk = s.recv(16384)
                        if chunk:
                            cmd_response += chunk
                            cmd_start_time = time.time() # Reset timeout if we keep receiving data
                        else:
                            break
                    except BlockingIOError:
                        if cmd_response and (time.time() - cmd_start_time > 0.5): break
                        time.sleep(0.1)
                
                if cmd_response:
                    # Log the response (it might be large, we just print the start/end or length if it was production)
                    print(f" -> Server Response received ({len(cmd_response)} bytes)")
                else:
                    show_warning(f"No response received for command: {cmd}")
                s.setblocking(True)

    except Exception as e:
        log_error_and_exit(f"Failed to transmit data to server on port {port}. Error: {str(e)}")


def execute_profile(profile_name):
    port = find_active_server_port()
    if not port:
        log_error_and_exit("Could not detect an active Focusrite Control Server instance.")

    # Save port to config if it's new
    if port != CONFIG["network"].get("last_successful_port"):
        CONFIG["network"]["last_successful_port"] = port
        
        # Also update LOADED_CONFIG to persist it without filling in defaults
        if "network" not in LOADED_CONFIG:
            LOADED_CONFIG["network"] = {}
        LOADED_CONFIG["network"]["last_successful_port"] = port
        save_config(LOADED_CONFIG)

    commands = CONFIG["profiles"].get(profile_name)
    if not commands:
        log_error_and_exit(f"Profile '{profile_name}' not found in configuration.")

    print(f"Executing profile: {profile_name}...")
    execute_tcp_stream(port, commands)


if __name__ == "__main__":
    mode = "routing_playback_only"
    if len(sys.argv) >= 2:
        mode = sys.argv[1]

    try:
        execute_profile(mode)
    except Exception as e:
        log_error_and_exit(f"An unexpected runtime exception occurred:\n{str(e)}")

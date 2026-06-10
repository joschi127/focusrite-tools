import re
import sys
import os
import time
import random

import yaml

from focusrite_client import FocusriteClient, FocusriteClientError, find_active_server_port, parse_device_id

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
CONFIG_FILE_PATH = os.path.join(APP_DIR, "config.yml")
DEFAULT_CONFIG_FILE_PATH = os.path.join(APP_DIR, "config.default.yml")
LOG_FILE_PATH = os.path.join(APP_DIR, "error.log")


def show_warning(message):
    """Logs a warning to the console and shows a message box if on Windows."""
    print(f" -> WARNING: {message}")
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


def save_config(config):
    """Saves the current configuration to the YAML file."""
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except Exception:
        pass

def load_yaml(file_path, required=False):
    """Loads a YAML file and returns its content as a dictionary."""
    if not os.path.exists(file_path):
        message = f"Configuration file not found: {file_path}"
        if required:
            log_error_and_exit(message)
        else:
            print(f" -> WARNING: {message}")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        message = f"Reading configuration file failed: {file_path}. Error: {e}"
        if required:
            log_error_and_exit(message)
        else:
            print(f" -> WARNING: {message}")
    return {}

def load_config():
    """Loads config from YAML and merges with defaults from config.default.yml."""
    default_config = load_yaml(DEFAULT_CONFIG_FILE_PATH, required=True)
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

def ensure_client_key(config, loaded_config):
    """Return a stable client key, generating and persisting a random 8-digit one if not set yet.

    The client key identifies this client to the Focusrite Control Server and the user's approval is
    bound to it, so it must stay stable. If the configured value is still null (~), a random 8-digit
    key is generated once and written back to config.yml.
    """
    client_key = config["network"].get("client_key")
    if client_key:
        return client_key

    client_key = "".join(str(random.randint(0, 9)) for _ in range(8))
    config["network"]["client_key"] = client_key

    # Persist into config.yml without filling in the other defaults.
    if "network" not in loaded_config:
        loaded_config["network"] = {}
    loaded_config["network"]["client_key"] = client_key
    save_config(loaded_config)

    return client_key

# Load active configuration
CONFIG, LOADED_CONFIG = load_config()

# Helper accessors for clarity
HOST = CONFIG["network"]["host"]
PORT_START, PORT_END = CONFIG["network"]["port_range"]
TIMEOUT = CONFIG["network"]["timeout"]
CLIENT_KEY = ensure_client_key(CONFIG, LOADED_CONFIG)

def execute_commands(port, command_list):
    """Opens a single connection and runs the full protocol: handshake, device-subscribe, then the commands.

    All low-level server communication (correct length-prefix framing, handshake with `client-key`, the
    mandatory `<device-subscribe .. subscribe="true"/>` step and the receive loop) is handled by
    `FocusriteClient` in `focusrite_client.py`.
    """
    try:
        with FocusriteClient(HOST, port, timeout=5.0, client_key=CLIENT_KEY) as client:
            # 1. Handshake. The response carries the approval state; while authorised="false" the server
            #    silently ignores every <set> until the client is trusted in the Focusrite Control app.
            #    It also carries the device-arrival element with the actual device id.
            handshake_response = client.handshake()
            if b'authorised="false"' in handshake_response:
                show_warning(
                    "This client is not approved yet (authorised=\"false\"). The Focusrite Control Server "
                    "will ignore all commands until you approve this client in the Focusrite Control "
                    "desktop application.")
                sys.exit(1)

            # 2. Determine the actual device id from the device-arrival response so that the subscribe
            #    and <set> commands target the right device even when the server assigns an id != "1".
            devid = parse_device_id(handshake_response)
            print(f" -> Device id from server: {devid}")

            # 3. Subscribe to the device. REQUIRED before the server accepts any <set> command.
            client.subscribe(devid=devid)

            # 4. Send the actual commands. Replace any hardcoded devid in the command strings with the
            #    id received from the server, then send them. We do NOT read after each one - reading
            #    mid-stream interrupts the server's reconfiguration (this is what made routing-profile
            #    switches like "System Playback" fail).
            for cmd in command_list:
                if not cmd:
                    continue

                # Substitute the placeholder devid ("1") in the command with the actual server devid.
                cmd = re.sub(r'devid="\d+"', f'devid="{devid}"', cmd)
                print(f"Sending command: {cmd}")
                client.send_command(cmd)

            # 5. Read the server response ONCE after all commands have been sent, exactly like the standalone
            #    test script does. A connection reset here is an expected side effect of a routing-profile
            #    change, so we tolerate it instead of failing.
            try:
                state = client.receive()
                if state:
                    print(f" -> Commands sent; received {len(state)} bytes of device state.")
                    print(f" -> State dump:\n{state.decode('utf-8', errors='ignore')}")
                else:
                    print(" -> Commands sent (no state dump returned by the server).")
            except FocusriteClientError:
                print(" -> Commands sent; the server reset the connection while reconfiguring (expected).")

    except (FocusriteClientError, Exception) as e:
        log_error_and_exit(f"Failed to transmit data to server on port {port}. Error: {str(e)}")


def switch_to_profile(profile_name):
    port = find_active_server_port(
        HOST, PORT_START, PORT_END, TIMEOUT, CONFIG["network"].get("last_successful_port"))
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

    print(f"Switching to profile: {profile_name}...")
    execute_commands(port, commands)


if __name__ == "__main__":
    mode = "computer"
    if len(sys.argv) >= 2:
        mode = sys.argv[1]

    try:
        switch_to_profile(mode)
    except Exception as e:
        log_error_and_exit(f"An unexpected runtime exception occurred:\n{str(e)}")

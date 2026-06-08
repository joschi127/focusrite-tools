import os
import socket
import time

def send_focusrite_snapshot(snapshot_path, host="127.0.0.1", port=49673):
    # 1. Ensure absolute native windows slashes
    clean_path = os.path.normpath(snapshot_path)
    
    # 2. Build the core XML command string
    xml_command = f'<client_command type="load_snapshot" file="{clean_path}"/>'
    
    # 3. FIX: Append the mandatory '\n' token to the end of the payload string
    # This signals the Focusrite Server to instantly process the buffer.
    payload = f"Length={len(xml_command):06d} {xml_command}\n"
    
    print(f"Connecting to Focusrite Control Server on {host}:{port}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)
            s.connect((host, port))
            
            # Focusrite servers often dump their current state immediately upon connection.
            # We set a non-blocking temporary window to flush out any initial greeting data.
            s.setblocking(False)
            try:
                time.sleep(0.1)
                s.recv(8192)  # Clear the initial greeting buffer
            except BlockingIOError:
                pass
            s.setblocking(True)
            
            print("Sending snapshot load command (with newline delimiter)...")
            s.sendall(payload.encode('utf-8'))
            
            print("Awaiting server processing and response...")
            time.sleep(0.3) 
            
            try:
                response = s.recv(4096).decode('utf-8', errors='ignore')
                if response:
                    print(f"\n[SERVER RESPONSE]:\n{response}")
                else:
                    print("\n[SERVER RESPONSE]: Connection closed. (Command accepted!)")
            except socket.timeout:
                print("\n[SERVER RESPONSE]: No error returned, but socket timed out.")
                
    except Exception as e:
        print(f"Socket Communication Error: {e}")

# Test with your explicit path
snapshot_file = r"C:\Program Files\Focusrite Swither\playback_only.ff"
send_focusrite_snapshot(snapshot_file)
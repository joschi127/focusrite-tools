import socket
import time
import re

#
# Minimalistic script to send handshake and keepalive commands to a Focusrite Control Server and receive the
# client-details, device-arrival and set response XML data.
#
# Also see `docs/focusrite_control_api/focusrite_control_api.md` for more information.
#

def send_test(host="192.168.5.27", port=49673):
    # 2. Build the core XML command string
    xml_handshake = '<client-details hostname="Junie" client-name="FocusriteSwitcher" client-id="123456"/>'
    xml_keepalive = '<set devid="1"><keep-alive/></set>'
    
    # Example: SET Analogue 1 Mode to 'Inst'
    #xml_command = '<set devid="1"><item id="799" value="Inst"/></set>'
    
    # Example: SET Mix A Input 1 Gain to -10.0 dB
    xml_command = '<set devid="1"><item id="55" value="-10.0"/></set>'

    # Example: SET Analogue 1 Muted to true
    #xml_command = '<set devid="1"><item id="57" value="true"/></set>'

    # FIX: Append the mandatory '\n' token to the end of the payload string
    # This signals the Focusrite Server to instantly process the buffer.
    payload_handshake = f"Length={len(xml_handshake):06d} {xml_handshake}\n"
    payload_keepalive = f"Length={len(xml_keepalive):06d} {xml_keepalive}\n"
    payload_command = f"Length={len(xml_command):06d} {xml_command}\n"
    
    print(f"Connecting to Focusrite Control Server on {host}:{port}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10.0)
            s.connect((host, port))
            
            # Sending handshake
            print("Sending handshake...")
            s.sendall(payload_handshake.encode('utf-8'))
            time.sleep(0.5)

            # Sending keep-alive (which will give us the current state of the device)
            print("Sending keep-alive...")
            s.sendall(payload_keepalive.encode('utf-8'))
            time.sleep(0.5)

            # Sending command
            print(f"Sending command: {xml_command}")
            s.sendall(payload_command.encode('utf-8'))
            time.sleep(0.5)

            # Receive responses
            print("Awaiting responses...")
            response = b""
            start_time = time.time()
            while time.time() - start_time < 5.0:
                try:
                    s.setblocking(False)
                    chunk = s.recv(16384)
                    if chunk:
                        response += chunk
                        start_time = time.time() # Reset timeout on data
                    else:
                        break
                except (BlockingIOError, socket.error):
                    if response and (time.time() - start_time > 0.5): break
                    time.sleep(0.1)

            if response:
                decoded_response = response.decode('utf-8', errors='ignore')
                print(f"\n[SERVER RESPONSE]:\n{decoded_response}")

                # Extract values for IDs 55, 798 and 799
                print("\n[EXTRACTED VALUES]:")
                for target_id in ["55", "57", "798", "799"]:
                    # Find all occurrences and take the last one (most recent state)
                    matches = re.findall(f'(<item id="{target_id}" value="([^"]*)"/>)', decoded_response)
                    if matches:
                        print(f"ID {target_id}: {matches[-1]}")
                    else:
                        print(f"ID {target_id}: Not found")
            else:
                print("\n[SERVER RESPONSE]: No data received.")
                
    except Exception as e:
        print(f"Socket Communication Error: {e}")

# Test with your explicit path
send_test()

import socket
import time

#
# Minimalistic script to send handshake and keepalive commands to a Focusrite Control Server and receive the
# client-details, device-arrival and set response XML data.
#
# Also see `docs/focusrite_control_api/focusrite_control_api.md` for more information.
#

def send_test(host="192.168.5.27", port=49673):
    # 2. Build the core XML command string
    handshake = '<client-details hostname="Junie" client-name="FocusriteSwitcher" client-id="123456"/>'
    xml_command = '<set devid="1"><keep-alive/></set>'
    
    # Example: SET Analogue 1 Mode to 'Line'
    xml_command2 = '<set devid="1"><item id="799" value="Line"/></set>'
    
    # Example: SET Mix A Input 1 Gain to -10.0 dB
    # xml_command2 = '<set devid="1"><item id="55" value="-10.0"/></set>'
    
    # 3. FIX: Append the mandatory '\n' token to the end of the payload string
    # This signals the Focusrite Server to instantly process the buffer.
    payload_handshake = f"Length={len(handshake):06d} {handshake}\n"
    payload_command = f"Length={len(xml_command):06d} {xml_command}\n"
    payload_command2 = f"Length={len(xml_command2):06d} {xml_command2}\n"
    
    print(f"Connecting to Focusrite Control Server on {host}:{port}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10.0)
            s.connect((host, port))
            
            # 4. Handshake
            print("Sending handshake...")
            s.sendall(payload_handshake.encode('utf-8'))
            
            # The server will send a lot of data now.
            # We must be ready to receive it, otherwise the server might close the connection
            # if we try to send more commands without consuming the buffer.
            print("Awaiting responses...")
            s.settimeout(5.0)
            received_state = False
            try:
                while True:
                    chunk = s.recv(16384)
                    if not chunk: break
                    if b"</set>" in chunk:
                        received_state = True
                        print("Received full state dump.")
                        # After state dump, we can try to send our command
                        print("Sending SET command...")
                        s.sendall(payload_command2.encode('utf-8'))
                    
                    # Also send keep-alives periodically if this was a long-running script
            except socket.timeout:
                if not received_state:
                    print("Timeout waiting for state dump. Server might be unresponsive.")
                else:
                    print("Done receiving for now.")
            except ConnectionResetError:
                print("Connection reset by peer. This often happens when sending invalid SET commands.")
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"Socket Communication Error: {e}")

# Test with your explicit path
send_test()

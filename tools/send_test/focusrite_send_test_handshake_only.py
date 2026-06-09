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
    xml_command2 = '<set devid="1"><item id="799" value="Inst" /></set>'

    # 3. FIX: Append the mandatory '\n' token to the end of the payload string
    # This signals the Focusrite Server to instantly process the buffer.
    payload_handshake = f"Length={len(handshake):06d} {handshake}\n"
    payload_command = f"Length={len(xml_command):06d} {xml_command}\n"
    payload_command2 = f"Length={len(xml_command2):06d} {xml_command2}\n"

    print(f"Connecting to Focusrite Control Server on {host}:{port}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((host, port))

            # 4. Handshake
            print("Sending handshake...")
            s.sendall(payload_handshake.encode('utf-8'))

            print("Sending command...")
            s.sendall(payload_command.encode('utf-8'))

            #print("Sending command 2...")
            #s.sendall(payload_command2.encode('utf-8'))

            print("Awaiting response...")
            response = b""
            start_time = time.time()
            # Extended timeout for the full state dump which can be large
            while time.time() - start_time < 3.0:
                try:
                    s.setblocking(False)
                    chunk = s.recv(16384)
                    if chunk:
                        response += chunk
                        start_time = time.time() # Reset timeout on data
                    else:
                        break
                except BlockingIOError:
                    if response and (time.time() - start_time > 0.5): break
                    time.sleep(0.1)

            if response:
                print(f"\n[SERVER RESPONSE]:\n{response.decode('utf-8', errors='ignore')}")
            else:
                print("\n[SERVER RESPONSE]: No data received.")

    except Exception as e:
        print(f"Socket Communication Error: {e}")

# Test with your explicit path
send_test()

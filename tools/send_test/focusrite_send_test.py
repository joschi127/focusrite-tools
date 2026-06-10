import socket
import time
import re

#
# Minimalistic script to send handshake, device-subscribe, keepalive and set commands to a Focusrite Control Server
# and receive the client-details, device-arrival and set response XML data.
#
# Also see `docs/focusrite_control_api/focusrite_control_api.md` for more information.
#
# IMPORTANT protocol details (confirmed against the reference implementation
# https://github.com/bitfocus/companion-module-focusrite-clarett/blob/main/focusrite-client.js):
#
# 1. Framing is a PREFIX, not a suffix: `Length=XXXXXX <xml>` where XXXXXX is the byte length of the XML
#    payload encoded as a 6-digit, zero-padded, UPPERCASE HEXADECIMAL number. There is NO trailing '\n'.
# 2. The keep-alive payload is a bare `<keep-alive/>` element (it does not need to be wrapped in `<set>`).
# 3. A client MUST subscribe to a device before the server will accept and apply any `<set>` command for that
#    device. The subscribe element REQUIRES the `subscribe="true"` attribute:
#    `<device-subscribe devid="N" subscribe="true"/>`. Sending a bare `<device-subscribe devid="N"/>` (without
#    `subscribe="true"`) does NOT establish a real subscription, so the server silently ignores every `<set>`
#    we send afterwards - which is exactly why our earlier attempts looked like they were "ignored".
# 4. The `<set>` syntax itself is correct: `<set devid="N"><item id="X" value="V"/></set>`. There is no
#    `<setvalue>` or similar command - the server's own state dump uses the very same `<item id=.. value=.."/>`
#    elements, confirmed against the authentic reverse-engineered client (raduvarga/Focusrite-Midi-Control).
# 5. *** THE ACTUAL REASON OUR <set> COMMANDS WERE IGNORED ***: the client must be APPROVED (trusted) inside the
#    Focusrite Control desktop application before the server will apply ANY <set>. After the handshake the server
#    replies with <approval ... authorised="false"/> until the user approves this client in Focusrite Control.
#    While authorised="false", reads/handshake/subscribe all still work, but every <set> is silently ignored.
#    The approval is bound to the client-key (here "12345678"); keep it stable so you only have to approve once.
#    Open Focusrite Control -> the new remote client appears and must be allowed/trusted; then re-run this script
#    and authorised will become "true" and the value changes will take effect.
#


def frame(xml: str) -> str:
    """Wrap an XML payload with the mandatory length PREFIX used by the Focusrite Control Server.

    Format: `Length=XXXXXX <xml>` where XXXXXX is the payload byte length as a 6-digit uppercase hex number.
    Note: there is intentionally NO trailing newline character.
    """
    length = len(xml.encode("utf-8"))
    return f"Length={length:06X} {xml}"


def send_test(host="192.168.5.27", port=49673):
    # 1. Build the core XML command strings
    xml_handshake = '<client-details hostname="focusrite-tools" client-key="12345678"/>'
    xml_keepalive = '<keep-alive/>'

    payload_handshake = frame(xml_handshake)
    payload_keepalive = frame(xml_keepalive)

    print(f"Connecting to Focusrite Control Server on {host}:{port}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10.0)
            s.connect((host, port))

            # Sending handshake (gives us the client-details / approval and device-arrival response)
            print("Sending handshake...")
            s.sendall(payload_handshake.encode('utf-8'))
            time.sleep(0.5)

            # Read the initial response to obtain the device-arrival element and parse the device id.
            # The server may send client-details + device-arrival as one or two separate TCP writes.
            handshake_response = b""
            handshake_start = time.time()
            while time.time() - handshake_start < 2.0:
                try:
                    s.setblocking(False)
                    chunk = s.recv(16384)
                    if chunk:
                        handshake_response += chunk
                        handshake_start = time.time()
                    else:
                        break
                except (BlockingIOError, socket.error):
                    if handshake_response and (time.time() - handshake_start > 0.3):
                        break
                    time.sleep(0.05)
            s.setblocking(True)

            # Parse the actual device id from the device-arrival element so that all subsequent
            # subscribe and <set> commands target the correct device regardless of the id assigned
            # by the server (it may be "2" or higher instead of the expected "1").
            # NOTE: the regex must match <device id="N" directly (not bus-id="0" or other
            # attributes that contain "id=" inside the same tag).
            handshake_text = handshake_response.decode('utf-8', errors='ignore')
            # Primary: <device-arrival ...><device id="N"  (most specific, avoids false positives)
            devid_match = re.search(r'<device-arrival[^>]*>\s*<device\s+id="(\d+)"', handshake_text)
            if not devid_match:
                # Fallback: bare <device id="N" anywhere (no preceding attributes that could confuse)
                devid_match = re.search(r'<device\s+id="(\d+)"', handshake_text)
            if devid_match:
                devid = devid_match.group(1)
            else:
                devid = "1"
                print("WARNING: Could not parse device id from server response. "
                      "Falling back to '1'. Commands may fail if the server uses a different id.")
            print(f"Device id from server: {devid}")

            # Build device-specific command strings using the detected devid.
            xml_subscribe = f'<device-subscribe devid="{devid}" subscribe="true"/>'

            # Example: Switch to preset '8 Channel Analogue'
            xml_command1 = f'<set devid="{devid}"><item id="6" value="8 Channel Analogue"/></set>'

            # Example: SET Analogue 1 Mode to 'Inst'
            xml_command2 = f'<set devid="{devid}"><item id="799" value="Inst"/></set>'

            # Example: SET Mix A Input 1 Gain to -10.0 dB
            xml_command3 = f'<set devid="{devid}"><item id="55" value="-10.0"/></set>'

            # Subscribing to the device. This is REQUIRED before the server will accept any `<set>` command.
            print("Sending device-subscribe...")
            s.sendall(frame(xml_subscribe).encode('utf-8'))
            time.sleep(0.5)

            # Sending command1
            print(f"Sending command1: {xml_command1}")
            s.sendall(frame(xml_command1).encode('utf-8'))
            time.sleep(0.5)

            # Sending command2
            print(f"Sending command2: {xml_command2}")
            s.sendall(frame(xml_command2).encode('utf-8'))
            time.sleep(0.5)

            # Sending command3
            print(f"Sending command3: {xml_command3}")
            s.sendall(frame(xml_command3).encode('utf-8'))
            time.sleep(0.5)

            # Sending keep-alive (which will give us the current state of the device)
            print("Sending keep-alive...")
            s.sendall(payload_keepalive.encode('utf-8'))
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

                # Check the approval / authorisation state. This is the gate that decides whether the server
                # actually APPLIES our <set> commands. While authorised="false" every <set> is silently ignored.
                print("\n[APPROVAL STATUS]:")
                auth_matches = re.findall(r'authorised="([^"]*)"', decoded_response)
                if auth_matches:
                    authorised = auth_matches[-1]
                    print(f"authorised = {authorised}")
                    if authorised != "true":
                        print("  -> This client is NOT approved yet, so the server will IGNORE every <set> command.")
                        print("  -> Approve/trust this client (client-key) inside the Focusrite Control desktop")
                        print("     application, then re-run this script. Value changes only take effect once")
                        print("     authorised becomes \"true\".")
                else:
                    print("No <approval> element found in the response.")

                # Extract values for IDs 55, 57, 798 and 799
                print("\n[EXTRACTED VALUES]:")
                for target_id in ["6", "55", "798", "799"]:
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

import re
import socket
import time

#
# Reusable client for talking to the Focusrite Control Server.
#
# This module centralises all server communication so that the different tools (e.g. the switcher) share a
# single, correct protocol implementation. The protocol details below were reverse-engineered and verified
# live against a real Scarlett 18i8 server. See `docs/focusrite_control_api/focusrite_control_api.md` and the
# standalone testing script `tools/send_test/focusrite_send_test.py` for the full background.
#
# IMPORTANT protocol details:
#
# 1. Framing is a PREFIX, not a suffix: `Length=XXXXXX <xml>` where XXXXXX is the byte length of the XML
#    payload encoded as a 6-digit, zero-padded, UPPERCASE HEXADECIMAL number. There is NO trailing '\n'.
# 2. The keep-alive payload is a bare `<keep-alive/>` element.
# 3. A client MUST subscribe to a device before the server will accept and apply any `<set>` command for that
#    device. The subscribe element REQUIRES the `subscribe="true"` attribute:
#    `<device-subscribe devid="N" subscribe="true"/>`.
# 4. The `<set>` syntax is `<set devid="N"><item id="X" value="V"/></set>`.
# 5. The client must be APPROVED (trusted) inside the Focusrite Control desktop application before the server
#    will apply ANY `<set>`. Until then the handshake response reports `authorised="false"` and every `<set>`
#    is silently ignored. The approval is bound to the `client-key`, so keep it stable.
#

DEFAULT_HANDSHAKE_HOSTNAME = "focusrite-tools"
DEFAULT_CLIENT_KEY = "12345678"
DEVICE_ID_FALLBACK = "1"


def parse_device_id(response):
    """Extract the device id from a ``device-arrival`` server response.

    Looks for the ``<device-arrival><device id="N" .../>`` element and returns the top-level
    device ``id`` attribute as a string.  The search is intentionally narrow:

    1. First tries ``<device-arrival … ><device id="N"`` (most specific – avoids false positives
       from other ``<device-…>`` elements or attributes like ``bus-id="0"`` in the same tag).
    2. Falls back to a bare ``<device id="N"`` match (handles non-standard server responses).

    Returns ``DEVICE_ID_FALLBACK`` (``"1"``) and prints a warning when no match is found so
    that callers can always use the return value without extra ``None``-checks.

    Args:
        response: raw server response as ``bytes`` or ``str``.
    Returns:
        Device id string, e.g. ``"1"`` or ``"2"``.
    """
    if isinstance(response, bytes):
        response = response.decode("utf-8", errors="ignore")
    # Primary: find <device id="N" directly inside a <device-arrival> element.
    match = re.search(r'<device-arrival[^>]*>\s*<device\s+id="(\d+)"', response)
    if match:
        return match.group(1)
    # Fallback: bare <device id="N" anywhere in the response (no other attributes before id=).
    match = re.search(r'<device\s+id="(\d+)"', response)
    if match:
        return match.group(1)
    print(
        "WARNING: parse_device_id – could not find device id in server response. "
        "Falling back to '{}'. Commands may fail if the server uses a different id.".format(
            DEVICE_ID_FALLBACK))
    return DEVICE_ID_FALLBACK


def frame(xml):
    """Wrap an XML payload with the mandatory length PREFIX used by the Focusrite Control Server.

    Format: `Length=XXXXXX <xml>` where XXXXXX is the payload byte length as a 6-digit uppercase hex number.
    Note: there is intentionally NO trailing newline character.
    """
    length = len(xml.encode("utf-8"))
    return "Length={:06X} {}".format(length, xml)


class FocusriteClientError(Exception):
    """Raised when communication with the Focusrite Control Server fails."""


class FocusriteClient:
    """Handles all TCP communication with a local Focusrite Control Server.

    Typical usage::

        client = FocusriteClient(host, port)
        client.connect()
        client.handshake()
        client.subscribe(devid="1")
        client.send_command('<set devid="1"><item id="55" value="-10.0"/></set>')
        client.close()

    or simply use it as a context manager.
    """

    def __init__(self, host, port, timeout=5.0,
                 hostname=DEFAULT_HANDSHAKE_HOSTNAME, client_key=DEFAULT_CLIENT_KEY):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.hostname = hostname
        self.client_key = client_key
        self._socket = None

    # -- Connection lifecycle ---------------------------------------------------------------------------

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def connect(self):
        """Open the TCP connection to the server."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)
            self._socket.connect((self.host, self.port))
        except Exception as e:
            self._socket = None
            raise FocusriteClientError(
                "Could not connect to Focusrite Control Server on {}:{}. Error: {}".format(
                    self.host, self.port, e))

    def close(self):
        """Close the TCP connection if it is open."""
        if self._socket is not None:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    # -- Protocol steps ---------------------------------------------------------------------------------

    def handshake(self, wait=0.5):
        """Send the client-details handshake. Returns the (possibly empty) initial server response.

        The response typically contains a ``<device-arrival>`` element from which the active device
        id can be read with :func:`parse_device_id`.
        """
        xml = '<client-details hostname="{}" client-key="{}"/>'.format(self.hostname, self.client_key)
        self._send(xml)
        if wait:
            time.sleep(wait)
        return self._drain()

    def subscribe(self, devid="1", wait=0.5):
        """Subscribe to a device. REQUIRED before the server accepts any `<set>` command for it.

        IMPORTANT: we intentionally do NOT drain the socket here. After a `<device-subscribe>` the
        server sends a large full-state dump (~100 KB). Reading it triggers the server to reset the
        subscription context, which causes the server to close the TCP connection as soon as the
        first `<set>` command is processed. By skipping the drain the state dump remains buffered
        in the OS receive buffer and is collected together with the command responses by the final
        `receive()` call — exactly as the reference send_test script does.
        """
        xml = '<device-subscribe devid="{}" subscribe="true"/>'.format(devid)
        self._send(xml)
        if wait:
            time.sleep(wait)

    def send_command(self, xml, wait=0.5):
        """Send a single raw XML command (e.g. a `<set>` element).

        IMPORTANT: this intentionally does NOT read from the socket. The reference test script
        (`tools/send_test/focusrite_send_test.py`) sends all commands first and only reads the server
        response ONCE at the end. Reading after every command (as we used to) consumes/interrupts the
        server's reconfiguration stream and is why routing-profile switches like `System Playback` failed.
        Call `receive()` once after all commands have been sent to collect the response.
        """
        self._send(xml)
        if wait:
            time.sleep(wait)

    def keep_alive(self, wait=0.5):
        """Send a bare `<keep-alive/>` element (pulls the current state dump on the next `receive()`)."""
        self.send_command('<keep-alive/>', wait=wait)

    def receive(self, read_timeout=5.0):
        """Read the server response ONCE, until the server goes quiet for ``read_timeout`` seconds.

        This mirrors the standalone test script: send everything first, then read a single time. Returns
        the raw response bytes (possibly empty).
        """
        return self._receive(read_timeout)

    # -- Low level helpers ------------------------------------------------------------------------------

    def _send(self, xml):
        if self._socket is None:
            raise FocusriteClientError("Not connected to a Focusrite Control Server.")
        payload = frame(xml)
        try:
            self._socket.sendall(payload.encode("utf-8"))
        except Exception as e:
            raise FocusriteClientError("Failed to send data to server: {}".format(e))

    def _drain(self, read_timeout= 1.0):
        """Read any immediately available data without blocking for long."""
        return self._receive(read_timeout)

    def _receive(self, read_timeout = 5.0):
        """Receive data from the server until it goes quiet for ``read_timeout`` seconds."""
        if self._socket is None:
            raise FocusriteClientError("Not connected to a Focusrite Control Server.")

        response = b""
        start_time = time.time()
        while time.time() - start_time < read_timeout:
            try:
                self._socket.setblocking(False)
                chunk = self._socket.recv(16384)
                if chunk:
                    response += chunk
                    start_time = time.time()  # Reset timeout on data
                else:
                    break
            except (BlockingIOError, socket.error):
                if response and (time.time() - start_time > 0.5):
                    break
                time.sleep(0.1)
        try:
            self._socket.setblocking(True)
        except Exception:
            pass
        return response


def find_active_server_port(host, port_start, port_end, timeout, last_port=None):
    """Scan the local TCP port range for a running Focusrite Control Server.

    Tries ``last_port`` first (if given) to speed up detection, then scans the range. Returns the first
    open port or ``None`` if no server was found.
    """
    if last_port:
        print("Trying last successful port: {}...".format(last_port))
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                if s.connect_ex((host, last_port)) == 0:
                    print(" -> Found Focusrite Control Server on last saved successful port {}".format(last_port))
                    return last_port
        except Exception:
            pass

    print("Scanning local TCP ports {}-{}...".format(port_start, port_end))
    for port in range(port_start, port_end + 1):
        if port == last_port:
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                if s.connect_ex((host, port)) == 0:
                    print(" -> Found Focusrite Control Server on TCP port {}".format(port))
                    return port
        except Exception:
            continue
    return None

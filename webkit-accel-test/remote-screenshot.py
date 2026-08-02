#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import json

output_file = sys.argv[1] if len(sys.argv) > 1 else "screenshot.png"
ip = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("IP", "192.168.50.86")

print(f"Triggering screenshot on {ip} via JS API...")

py_remote = """import urllib.request, json, socket, base64, sys

try:
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    targets = json.loads(req.read().decode())
    if not targets:
        print("Error: No targets found on 127.0.0.1:9222", file=sys.stderr)
        sys.exit(1)

    ws_url = targets[0]["webSocketDebuggerUrl"]
    host_port, path = ws_url.replace("ws://", "").split("/", 1)
    host, port = host_port.split(":")

    s = socket.create_connection((host, int(port)))
    key = base64.b64encode(b"1234567890123456").decode()
    req_headers = (
        f"GET /{path} HTTP/1.1\\r\\n"
        f"Host: {host_port}\\r\\n"
        f"Upgrade: websocket\\r\\n"
        f"Connection: Upgrade\\r\\n"
        f"Sec-WebSocket-Key: {key}\\r\\n"
        f"Sec-WebSocket-Version: 13\\r\\n\\r\\n"
    )
    s.sendall(req_headers.encode())
    s.recv(4096)

    js_eval = '''
    new Promise((resolve) => {
        function runSlot(api) {
            if (api && typeof api.take_screenshot === 'function') {
                api.take_screenshot(resolve);
            } else {
                resolve("error: take_screenshot method missing");
            }
        }

        if (window.systemApi && typeof window.systemApi.take_screenshot === 'function') {
            runSlot(window.systemApi);
        } else if (typeof qt !== 'undefined' && qt.webChannelTransport) {
            if (typeof QWebChannel !== 'undefined') {
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    window.systemApi = channel.objects.systemApi;
                    runSlot(window.systemApi);
                });
            } else {
                var script = document.createElement('script');
                script.src = 'qrc:///qtwebchannel/qwebchannel.js';
                script.onload = function() {
                    new QWebChannel(qt.webChannelTransport, function(channel) {
                        window.systemApi = channel.objects.systemApi;
                        runSlot(window.systemApi);
                    });
                };
                script.onerror = function() { resolve("error: failed to load qwebchannel.js"); };
                document.head.appendChild(script);
            }
        } else {
            resolve("error: systemApi and qt.webChannelTransport unavailable");
        }
    })
    '''

    msg = json.dumps({
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {"expression": js_eval, "awaitPromise": True}
    })
    payload = msg.encode("utf-8")
    length = len(payload)
    frame = bytearray([0x81])
    if length < 126:
        frame.append(0x80 | length)
    elif length < 65536:
        frame.append(0x80 | 126)
        frame.extend(length.to_bytes(2, "big"))
    frame.extend(b"\\x00\\x00\\x00\\x00")
    frame.extend(payload)
    s.sendall(frame)

    resp = s.recv(4096)
    s.close()
    print(resp.decode(errors="replace"))
except Exception as e:
    print(f"Remote error: {e}", file=sys.stderr)
    sys.exit(1)
"""

res = subprocess.run(["ssh", f"ark@{ip}", "python3 -"], input=py_remote, capture_output=True, text=True)
if res.returncode != 0:
    print(f"Error triggering screenshot via CDP over SSH: {res.stderr.strip()}")
    sys.exit(1)

print(f"[DEBUG] Remote CDP response: {res.stdout.strip()}")

time.sleep(0.3)

print("Fetching screenshot image...")
try:
    img_res = subprocess.run(["ssh", f"ark@{ip}", "cat /tmp/screenshot.png"], capture_output=True, check=True)
    if len(img_res.stdout) > 0:
        with open(output_file, "wb") as f:
            f.write(img_res.stdout)
        print(f"Successfully captured screenshot to {output_file}")
    else:
        print("Error: Empty screenshot file received.")
        sys.exit(1)
except Exception as e:
    print(f"Error fetching screenshot file: {e}")
    sys.exit(1)

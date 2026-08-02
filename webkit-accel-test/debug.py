#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import urllib.request
import json
import socket
import base64

ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.50.86"
user = "ark"

print(f"Establishing SSH tunnel to {user}@{ip}...")
ssh_cmd = [
    "ssh",
    "-L",
    "9222:localhost:9222",
    f"{user}@{ip}",
    "echo 'SSH tunnel active. Press Ctrl+C to close.' && sleep infinity"
]
ssh_proc = subprocess.Popen(ssh_cmd)

for attempt in range(30):
    try:
        s_test = socket.create_connection(("127.0.0.1", 9222), timeout=0.5)
        s_test.close()
        print("[DEBUG] SSH tunnel active on port 9222.")
        break
    except Exception:
        time.sleep(0.5)

print("Remote debugging will be available at chrome://inspect/#devices")

# Launch local Chromium with remote debugging port 9223
chrome_cmd = [
    "chromium-browser",
    "--remote-debugging-port=9223",
    "--user-data-dir=/tmp/r36s-debug-chrome-profile",
    "--remote-allow-origins=*",
]
subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("[DEBUG] Requesting new target from Chromium CDP on 9223...")
ws_url = None
inspect_target_id = None
initial_target_ids = []

for attempt in range(30):
    try:
        list_req = urllib.request.urlopen("http://127.0.0.1:9223/json/list")
        initial_targets = json.loads(list_req.read().decode())
        initial_target_ids = [t["id"] for t in initial_targets if "id" in t]

        url = "http://127.0.0.1:9223/json/new?chrome://inspect/%23devices"
        req = urllib.request.Request(url, method="PUT")
        target_data = json.loads(urllib.request.urlopen(req).read().decode())
        print(f"[DEBUG] /json/new response: {target_data}")
        ws_url = target_data.get("webSocketDebuggerUrl")
        inspect_target_id = target_data.get("id")
        if ws_url:
            break
    except Exception as e:
        print(f"[DEBUG] Attempt {attempt+1} failed: {e}")
        time.sleep(0.2)

if not ws_url:
    print("[DEBUG] Error: Failed to acquire webSocketDebuggerUrl")
else:
    print(f"[DEBUG] Connected target WS URL: {ws_url}")
    host_port, path = ws_url.replace("ws://", "").split("/", 1)
    host, port = host_port.split(":")
    print(f"[DEBUG] Connecting WebSocket to {host}:{port} path /{path}")
    s = socket.create_connection((host, int(port)))
    key = base64.b64encode(b"1234567890123456").decode()
    req_headers = (
        f"GET /{path} HTTP/1.1\r\n"
        f"Host: {host_port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n"
    )
    s.sendall(req_headers.encode())
    resp = s.recv(4096)
    resp_str = resp.decode(errors="replace")
    print(f"[DEBUG] WS handshake response:\n{resp_str}")

    msg_id = 1

    def send_ws_json(msg_obj):
        payload = json.dumps(msg_obj).encode("utf-8")
        length = len(payload)
        frame = bytearray([0x81])
        if length < 126:
            frame.append(0x80 | length)
        elif length < 65536:
            frame.append(0x80 | 126)
            frame.extend(length.to_bytes(2, "big"))
        frame.extend(b"\x00\x00\x00\x00")
        frame.extend(payload)
        s.sendall(frame)

    def recv_ws_json():
        hdr = s.recv(2)
        if not hdr or len(hdr) < 2:
            return None
        length = hdr[1] & 0x7f
        if length == 126:
            length = int.from_bytes(s.recv(2), "big")
        elif length == 127:
            length = int.from_bytes(s.recv(8), "big")
        data = bytearray()
        while len(data) < length:
            chunk = s.recv(length - len(data))
            if not chunk:
                break
            data.extend(chunk)
        return json.loads(data.decode("utf-8"))

    js_find_coords = """
    (function() {
      function findInspectBtn(root = document) {
        const els = Array.from(root.querySelectorAll("*"));
        for (const el of els) {
          if (el.shadowRoot) {
            const found = findInspectBtn(el.shadowRoot);
            if (found) return found;
          }
          if ((el.classList && el.classList.contains("action") &&
               el.getAttribute("action") === "inspect") ||
              (el.textContent && el.textContent.trim().toLowerCase() === "inspect"
               && el.children.length === 0)) {
            return el;
          }
        }
        return null;
      }
      const btn = findInspectBtn();
      if (!btn) return null;
      const rect = btn.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return null;
      return {x: Math.round(rect.left + rect.width / 2), y: Math.round(rect.top + rect.height / 2)};
    })()
    """

    coords = None
    for poll in range(20):
        try:
            msg_id += 1
            send_ws_json({
                "id": msg_id,
                "method": "Runtime.evaluate",
                "params": {"expression": js_find_coords, "returnByValue": True}
            })
            res = recv_ws_json()
            print(f"[DEBUG] Poll {poll+1} find inspect btn res: {res}")
            if res and "result" in res and "result" in res["result"]:
                val = res["result"]["result"].get("value")
                if val and "x" in val and "y" in val:
                    coords = val
                    break
        except Exception as e:
            print(f"[DEBUG] Poll {poll+1} error: {e}")
            break
        time.sleep(0.5)

    if coords:
        x, y = coords["x"], coords["y"]
        print(f"[DEBUG] Dispatching real mouse events at x={x}, y={y}...")
        msg_id += 1
        send_ws_json({
            "id": msg_id,
            "method": "Input.dispatchMouseEvent",
            "params": {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1}
        })
        time.sleep(0.05)
        msg_id += 1
        send_ws_json({
            "id": msg_id,
            "method": "Input.dispatchMouseEvent",
            "params": {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1}
        })
        print("[DEBUG] Mouse click dispatched!")
        time.sleep(1.5)
        for tid in [inspect_target_id] + initial_target_ids:
            if tid:
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:9223/json/close/{tid}")
                    print(f"[DEBUG] Closed target {tid}")
                except Exception as e:
                    print(f"[DEBUG] Failed to close target {tid}: {e}")
    else:
        print("[DEBUG] Could not find inspect button coordinates.")

    time.sleep(0.5)
    s.close()

try:
    ssh_proc.wait()
except KeyboardInterrupt:
    print("\nClosing SSH tunnel...")
    ssh_proc.terminate()

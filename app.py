#!/usr/bin/env python3
"""Minimal HTTP shipping service using only the Python standard library."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8080"))
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_MESSAGE = os.getenv("APP_MESSAGE", "Shipping Service")

class Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/api/shipping"):
            self._send(200, {
                "service": "shipping",
                "message": APP_MESSAGE,
                "version": APP_VERSION,
                "status": "ok",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        elif self.path == "/healthz":
            self._send(200, {"status": "healthy"})
        elif self.path == "/readyz":
            self._send(200, {"status": "ready"})
        else:
            self._send(404, {"error": "not_found", "path": self.path})

    def log_message(self, fmt, *args):
        # Keep standard HTTP access logs on stdout for Kubernetes log collection.
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"shipping service listening on {HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

import functools
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = "/Users/tysontran/Desktop/Smart Art Heritage"

class DevHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        if self.path in ("/v1/models", "/v1/models/status"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"data":[],"status":"ready"}')
            return
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        return super().do_GET()

class Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

print("serving", ROOT, flush=True)
Server(("127.0.0.1", 8080), DevHandler).serve_forever()

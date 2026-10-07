import functools
import socketserver
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = "/Users/tysontran/Desktop/Smart Art Heritage"


class Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


handler = functools.partial(SimpleHTTPRequestHandler, directory=ROOT)
print("serving", ROOT, flush=True)
Server(("127.0.0.1", 8080), handler).serve_forever()

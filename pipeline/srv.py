# servidor de teste com suporte a Range (como o GitHub Pages)
import http.server, socketserver, threading, os, functools, re
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        rng = self.headers.get("Range"); path = self.translate_path(self.path.split("?")[0])
        if rng and os.path.isfile(path):
            m = re.match(r"bytes=(\d+)-(\d+)?", rng); size = os.path.getsize(path); a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else size - 1
            self.send_response(206); self.send_header("Content-Type", self.guess_type(path)); self.send_header("Content-Range", f"bytes {a}-{b}/{size}"); self.send_header("Content-Length", str(b - a + 1)); self.send_header("Accept-Ranges", "bytes"); self.end_headers()
            with open(path, "rb") as f: f.seek(a); self.wfile.write(f.read(b - a + 1))
        else: super().do_GET()
def serve(root, port):
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    s = socketserver.ThreadingTCPServer(("127.0.0.1", port), functools.partial(H, directory=root)); threading.Thread(target=s.serve_forever, daemon=True).start(); return s

"""Local-only HTTP receiver for five provider-specific upload requests."""
import json
import os
import random
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        service = self.path.split("?", 1)[0].strip("/").split("/", 1)[0]
        if service not in {"wunderground", "weathercloud", "windy", "pwsweather", "metoffice"}:
            self.send_error(404, "Unknown mock service")
            return
        failed = random.random() < float(os.getenv("MOCK_FAILURE_RATE", "0"))
        code = 503 if failed else 200
        payload = json.dumps({"service": service, "accepted": not failed, "timestamp": datetime.now(timezone.utc).isoformat()}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        # Do not log query strings: these may contain dummy credentials.
        print(f"{service} HTTP {code}", flush=True)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

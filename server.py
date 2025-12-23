"""
The server is responsible for getting requests from the client and processing them according to policy rules
"""

import http.server
import json

class RequestHandler(http.server.BaseHTTPRequestHandler):
    # NOTE: avoid overriding __init__ since we dont need to setup unique variables for every single request

    def do_POST(self):
        if self.path == "/mitigate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            # NOTE: avoid using return that will send nothing to the client. Instead, use self.send_response and self.wfile.write
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return

            # Fetch mandatory fields
            prompt = data.get("prompt")
            user_id = data.get("user_id")

            if not prompt or not user_id:
                self.send_error(400, "Missing required fields: prompt and user_id")
                return

            # Fetch optional fields
            # NOTE: Use get() with default values to avoid crashing
            model = data.get("model", "gpt-4o")
            purpose = data.get("purpose", "general")
            meta_headers = data.get("headers", {})

            print(f"Received request: prompt={prompt}, user_id={user_id}, model={model}, purpose={purpose}, headers={meta_headers}")

            # Tell the client that the request was successful
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            # NOTE: end_headers() tells the browser the headers are done
            self.end_headers()
            # Convert the data to a JSON string and encode it to bytes
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")


if __name__ == "__main__":
    server = http.server.HTTPServer(("localhost", 8000), RequestHandler)
    server.serve_forever()
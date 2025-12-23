"""
The server is responsible for getting requests from the client and processing them according to policy rules
"""

import http.server
import json
import time
from collections import UserDict, deque
from policy import Policy


class RequestHandler(http.server.BaseHTTPRequestHandler):
    # NOTE: avoid overriding __init__ since we dont need to setup unique variables for every single request
    # Load the brain
    policy = Policy()

    # Keep last 20 history items 
    history = deque(maxlen=20)

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

            # Pass user prompt to the policy evaulate function
            policy_decision = self.policy.evaluate_prompt(prompt)

            # Create a new entry in the history
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": user_id,
                "prompt_in": prompt,
                "action": policy_decision["action"],
                "reason": policy_decision["reason"]
            }

            self.history.append(log_entry)

            # Build the response data for the client
            response_data = {
                "action": policy_decision["action"],
                "prompt_out": policy_decision["prompt_out"],
                "reason": policy_decision["reason"],
                "user_id": user_id,
            }

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
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        """Handle GET requests. Return the last N requests"""
        if self.path == "/history":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            # Convert history deque to a list so JSON can read it
            response = {"history": list(self.history)}

            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")


if __name__ == "__main__":
    server = http.server.HTTPServer(("localhost", 8000), RequestHandler)
    server.serve_forever()
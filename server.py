"""
The server is responsible for getting requests from the client and processing them according to policy rules
"""

import http.server
import json
import time
from collections import deque
from core.policy import Policy
from urllib.parse import urlparse, parse_qs


class RequestHandler(http.server.BaseHTTPRequestHandler):
    # NOTE: avoid overriding __init__ since we dont need to setup unique variables for every single request
    # Load the brain (class variable in order to load it once)
    policy = Policy()

    # Keep last 20 history items 
    history = deque(maxlen=100)

    # ========== END POINTS ========== #
    def do_POST(self):
        if self.path == "/mitigate":
            self.handle_mitigate()

        elif self.path == "/reload":
            self.handle_reload()

        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        """Handle GET requests with support for query parameters."""
        # Parse the URL cleanly (separates path from query params)
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/history":
            # Extract 'n' from query params (e.g., ?n=5)
            query_params = parse_qs(parsed_url.query)
            
            try:
                # Get 'n', default to ['20'], take the first item, convert to int
                limit = int(query_params.get("n", ["20"])[0])
            except (ValueError, TypeError):
                limit = 20

            # Get the data
            full_history = list(self.history)
            
            # If limit is 0 or negative, return everything (or handle as error)
            if limit > 0:
                response_data = full_history[-limit:]
            else:
                response_data = full_history[-20:]

            self._send_json({"history": response_data})
        else:
            self.send_error(404, "Not Found")

    # ========== HELPER FUNCTIONS ========== #
    def handle_mitigate(self):
        """Process the mitigation logic."""
        data = self._get_json_body()
        if data is None:
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

        # Pass user prompt to the policy evaulate function
        policy_decision = self.policy.evaluate_prompt(prompt)
        
        # Create a new entry in the history
        self._log_to_history(user_id, prompt, policy_decision)

        # Build the response data for the client
        response_data = {
            "action": policy_decision["action"],
            "prompt_out": policy_decision["prompt_out"],
            "reason": policy_decision["reason"],
            "user_id": user_id,
        }

        self._send_json(response_data)

    def handle_reload(self):
        """Handle the reload of the policy."""
        try:
            self.policy.load_policy()
            self._send_json({"message": "Policy reloaded successfully"})
        except Exception as e:
            self._send_json({"message": f"Failed to reload policy: {str(e)}"}, 500)

    def _get_json_body(self):
        """Helper to read and parse JSON body."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            return json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return None

    def _log_to_history(self, user_id, prompt, policy_decision):
        """Helper to log the request to the history."""
        # Create a new entry in the history
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id,
            "prompt_in": prompt,
            "action": policy_decision["action"],
            "reason": policy_decision["reason"]
        }

        self.history.append(log_entry)

    def _send_json(self, data, status=200):
        """Helper to standardize sending JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    

if __name__ == "__main__":
    # Bind to 0.0.0.0 in order for this to work on docker
    server = http.server.HTTPServer(("0.0.0.0", 8000), RequestHandler)
    print("Server started on port 8000...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()
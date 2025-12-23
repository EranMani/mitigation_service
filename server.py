"""
The server is responsible for getting requests from the client and processing them according to policy rules
"""

import http.server
import json
import time
import socketserver
import threading
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

    @classmethod
    def _log_to_history(cls, user_id, prompt, policy_decision):
        """Helper to log the request to the history."""
        # Create a new entry in the history
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id,
            "prompt_in": prompt,
            "action": policy_decision["action"],
            "reason": policy_decision["reason"]
        }

        cls.history.append(log_entry)

    def _send_json(self, data, status=200):
        """Helper to standardize sending JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    
class MockICAPHandler(socketserver.StreamRequestHandler):
    """
    A minimal mock ICAP adapter that listens on port 1344.
    It reuses the same Policy engine as the HTTP server.
    """

    """
    NOTE: Not using a web framework here. Just listening to a raw data stream.
    NOTE: No conversation is happening, like in a http.server request. We need to do the conversation manually.
    NOTE: b"204 .... " => tells python to treat this as raw bytes, not a string.
    NOTE: ISTag = ICAP Service Tag. It tells the proxy this file was scanned and so it doesnt need to ask the server again.
    """

    def handle(self):
        try:
            # 1. Read the raw request data, byte by byte
            self.data = self.rfile.readline().strip().decode("utf-8")
            print(f"[ICAP] Received request: {self.data}")

            if not self.data: return

            # 2. Extract Prompt
            # Input example: REQMOD icap://server/mitigate PROMPT=Hello World
            # Look for the "PROMPT=" marker
            if "PROMPT=" in self.data:
                # Split only once (1) just in case the prompt itself contains "PROMPT="
                prompt = self.data.split("PROMPT=", 1)[1]
            else:
                # Fallack. Use whole line as the prompt
                prompt = self.data

            # 3. Reuse the same policy engine instance
            decision = RequestHandler.policy.evaluate_prompt(prompt)

            RequestHandler._log_to_history("icap_client", prompt, decision)

            # 4. Send Response 
            # 204 = No modification needed (allow)
            # 200 = Modified version follows (redact/block)
            if decision["action"] == "allow":
                response = b"ICAP/1.0 204 No Content\r\n\r\n"

            else:
                header = b"ICAP/1.0 200 OK\r\nISTag: \"Mitigation-1.0\"\r\n\r\n"
                response = header + decision["prompt_out"].encode()

            self.wfile.write(response)
            print(f"[ICAP] Sent response: {response.decode('utf-8')}")
        except Exception as e:
            print(f"[ICAP] Error: {str(e)}")
            self.wfile.write(b"500 Internal Server Error\r\n")





if __name__ == "__main__":
    '''
    NOTE: Bind to 0.0.0.0 in order for this to work on docker
    NOTE: Analogy - we are building a kitchen that knows how to check food (prompts)
          Server 1 (HTTP): The Dining Room. Customers sit down, order politely, and get a full service meal.
          Server 2 (ICAP): The Drive-Thru. Cars pull up, shout raw orders, and get a quick bag of food.
          This code manages both servers at the same time. One Manager (Threading) keeping them both alive.

          Background Thread: Handles HTTP requests on port 8000.
          Main Thread: Handles ICAP requests on port 1344.
    '''

    # 1. Configure HTTP Server (Port 8000)
    http_server = http.server.HTTPServer(("0.0.0.0", 8000), RequestHandler)

    # 2. Configure ICAP Server (Port 1344)
    socketserver.TCPServer.allow_reuse_address = True
    icap_server = socketserver.TCPServer(("0.0.0.0", 1344), MockICAPHandler)

    # 3. Run them in parallel using threads
    print("Server started on port 8000...")
    # Run the http server in a separate thread, let the ICAP server run in the main thread
    # NOTE: Non-blocking operation. The main thread can still handle ICAP requests.
    http_thread = threading.Thread(target=http_server.serve_forever)
    # NOTE: A "Daemon" is a background worker that doesn't matter once the main boss leaves. It will be killed once the main program is done.
    http_thread.daemon = True
    http_thread.start()

    print("Starting ICAP (Mock) Server on port 1344...")
    try:
        # Main thread runs ICAP
        icap_server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        icap_server.shutdown()
        http_server.shutdown()
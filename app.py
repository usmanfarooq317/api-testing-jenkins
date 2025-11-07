# app.py
from flask import Flask, request, jsonify, render_template_string
import os
import time
import uuid

app = Flask(__name__)

# Simple in-memory "log" for demo
REQUEST_LOG = []

# HTML frontend (simple single page served by Flask)
INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>API Testing Jenkins</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; }
    .card { border:1px solid #ddd; padding:16px; margin-bottom:16px; border-radius:8px; }
    input, textarea { width: 100%; padding:8px; margin:8px 0; box-sizing:border-box; }
    button { padding:8px 16px; }
    pre { background:#f7f7f7; padding:12px; border-radius:6px; }
  </style>
</head>
<body>
  <h1>API Testing Jenkins (port 5090)</h1>
  <div class="card">
    <h3>Call secure API</h3>
    <label>X-Api-Key (required)</label>
    <input id="apikey" value="secret-key-123" />
    <label>X-Request-Id (required)</label>
    <input id="reqid" value="req-{{rid}}" />
    <label>JSON body (name)</label>
    <input id="name" value="Usman" />
    <button onclick="callApi()">Call /api/secure</button>
    <p>Response:</p>
    <pre id="out">-</pre>
  </div>

  <div class="card">
    <h3>Health & Logs</h3>
    <button onclick="fetch('/health').then(r=>r.text()).then(t=>alert(t))">Health check</button>
    <button onclick="fetch('/logs').then(r=>r.json()).then(j=>document.getElementById('out').textContent = JSON.stringify(j, null, 2))">Show recent logs</button>
  </div>

<script>
async function callApi() {
  const key = document.getElementById('apikey').value;
  const rid = document.getElementById('reqid').value;
  const name = document.getElementById('name').value;
  const resp = await fetch('/api/secure', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Api-Key': key,
      'X-Request-Id': rid
    },
    body: JSON.stringify({ name })
  });
  const text = await resp.text();
  document.getElementById('out').textContent = 'HTTP ' + resp.status + '\\n' + text;
}
</script>
</body>
</html>
""".replace("{{rid}}", str(uuid.uuid4())[:8])


# --- Backend endpoints ---

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/health")
def health():
    return "OK - port 5090", 200


@app.route("/logs")
def logs():
    # return last 20 requests
    return jsonify(REQUEST_LOG[-20:]), 200


@app.route("/api/secure", methods=["POST"])
def api_secure():
    """
    Secure endpoint that requires:
     - header: X-Api-Key (must equal SECRET_API_KEY)
     - header: X-Request-Id (non-empty)
     - body: JSON with "name" string (min 2 chars)
    Returns JSON with greeting and server info.
    """
    SECRET_API_KEY = os.environ.get("SECRET_API_KEY", "secret-key-123")

    headers = request.headers
    x_api_key = headers.get("X-Api-Key")
    x_req_id = headers.get("X-Request-Id")
    body = None
    try:
        body = request.get_json(force=True)
    except Exception:
        # bad json
        body = None

    record = {
        "time": int(time.time()),
        "client_ip": request.remote_addr,
        "headers": {
            "X-Api-Key": bool(x_api_key),
            "X-Request-Id": bool(x_req_id),
            "Content-Type": headers.get("Content-Type")
        },
        "body": body
    }

    # Store a short record
    REQUEST_LOG.append(record)

    # Validate headers
    if not x_api_key:
        return jsonify({"error": "Missing header X-Api-Key"}), 400
    if x_api_key != SECRET_API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    if not x_req_id:
        return jsonify({"error": "Missing header X-Request-Id"}), 400

    # Validate body
    if not body or not isinstance(body, dict):
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    name = body.get("name")
    if not name or not isinstance(name, str) or len(name.strip()) < 2:
        return jsonify({"error": "Invalid 'name' field; must be string length >= 2"}), 400

    # Success
    resp = {
        "message": f"Hello, {name.strip()}!",
        "request_id": x_req_id,
        "server_time": int(time.time())
    }
    return jsonify(resp), 200


# Small echo endpoint used for more tests
@app.route("/api/echo", methods=["GET", "POST"])
def echo():
    return jsonify({
        "method": request.method,
        "headers": dict(request.headers),
        "args": request.args,
        "body": request.get_json(silent=True)
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5090))
    # run with 0.0.0.0 so container exposes it
    app.run(host="0.0.0.0", port=port)

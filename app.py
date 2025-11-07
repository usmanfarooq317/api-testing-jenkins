# app.py
from flask import Flask, request, jsonify, render_template_string
import os
import time
import uuid
from datetime import datetime

app = Flask(__name__)

# Log file path (shared for Jenkins + API)
LOG_FILE = "test_results.txt"

def write_log(entry: str):
    """Append logs to test_results.txt with timestamps."""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {entry}\n")

# Simple in-memory "log" for demo
REQUEST_LOG = []

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


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/health")
def health():
    return "OK - port 5090", 200


@app.route("/logs")
def logs():
    return jsonify(REQUEST_LOG[-20:]), 200


@app.route("/api/secure", methods=["POST"])
def api_secure():
    SECRET_API_KEY = os.environ.get("SECRET_API_KEY", "secret-key-123")

    headers = request.headers
    x_api_key = headers.get("X-Api-Key")
    x_req_id = headers.get("X-Request-Id")

    try:
        body = request.get_json(force=True)
    except Exception:
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
    REQUEST_LOG.append(record)

    if not x_api_key:
        write_log(f"ERROR Missing X-Api-Key from {request.remote_addr}")
        return jsonify({"error": "Missing header X-Api-Key"}), 400
    if x_api_key != SECRET_API_KEY:
        write_log(f"ERROR Invalid X-Api-Key from {request.remote_addr}")
        return jsonify({"error": "Invalid API key"}), 401
    if not x_req_id:
        write_log(f"ERROR Missing X-Request-Id from {request.remote_addr}")
        return jsonify({"error": "Missing header X-Request-Id"}), 400
    if not body or not isinstance(body, dict):
        write_log(f"ERROR Invalid JSON body from {request.remote_addr}")
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    name = body.get("name")
    if not name or len(name.strip()) < 2:
        write_log(f"ERROR Invalid name field from {request.remote_addr}")
        return jsonify({"error": "Invalid 'name' field; must be string length >= 2"}), 400

    resp = {
        "message": f"Hello, {name.strip()}!",
        "request_id": x_req_id,
        "server_time": int(time.time())
    }

    write_log(f"SUCCESS API call by {name.strip()} with req_id={x_req_id}")
    return jsonify(resp), 200


@app.route("/api/echo", methods=["GET", "POST"])
def echo():
    data = {
        "method": request.method,
        "headers": dict(request.headers),
        "args": request.args,
        "body": request.get_json(silent=True)
    }
    write_log(f"ECHO endpoint called from {request.remote_addr}")
    return jsonify(data), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5090))
    app.run(host="0.0.0.0", port=port)

# app.py
from flask import Flask, request, jsonify, render_template_string, send_file, Response
import os
import time
import uuid
import json
from datetime import datetime

app = Flask(__name__)

# -------------------- Log File Setup -------------------- #
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "api-test-results.json")
os.makedirs(LOG_DIR, exist_ok=True)

# Ensure the log file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        json.dump([], f, indent=2)


# -------------------- Helper Function -------------------- #
def write_log(entry: dict):
    """Append structured log entries into logs/api-test-results.json"""
    entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Read existing logs
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(entry)

    # Write updated logs
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


# -------------------- Frontend HTML -------------------- #
INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>API Testing Jenkins Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; background:#f9f9f9; }
    .card { background:white; border:1px solid #ddd; padding:16px; margin-bottom:20px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.1);}
    input { width:100%; padding:8px; margin:6px 0; box-sizing:border-box; }
    button { padding:8px 14px; border:none; border-radius:5px; background:#007bff; color:white; cursor:pointer; }
    button:hover { background:#0056b3; }
    pre { background:#f3f3f3; padding:12px; border-radius:6px; overflow:auto; }
    a.download { text-decoration:none; color:white; background:#28a745; padding:8px 14px; border-radius:5px; margin-left:10px; }
    a.download:hover { background:#1e7e34; }
  </style>
</head>
<body>
  <h1>🚀 Jenkins Integrated API Testing Dashboard</h1>

  <div class="card">
    <h3>🔐 Call Secure API</h3>
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
    <h3>🩺 Health & Logs</h3>
    <button onclick="fetch('/health').then(r=>r.text()).then(t=>alert(t))">Health Check</button>
    <button onclick="showLogs()">Show Logs</button>
    <a class="download" href="/logs/full?download=1" target="_blank">⬇ Download Logs</a>
  </div>

  <div class="card">
    <h3>📜 Recent Logs</h3>
    <pre id="fullLogs">Click "Show Logs" to view logs here</pre>
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

async function showLogs() {
  const resp = await fetch('/logs/full');
  const text = await resp.text();
  document.getElementById('fullLogs').textContent = text;
}
</script>
</body>
</html>
""".replace("{{rid}}", str(uuid.uuid4())[:8])


# -------------------- Routes -------------------- #

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/health")
def health():
    return "OK - port 5090", 200


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
        "source": "frontend",
        "client_ip": request.remote_addr,
        "headers": dict(headers),
        "body": body,
        "endpoint": "/api/secure"
    }

    # Header validation
    if not x_api_key:
        record["result"] = "❌ Missing X-Api-Key"
        write_log(record)
        return jsonify({"error": "Missing header X-Api-Key"}), 400
    if x_api_key != SECRET_API_KEY:
        record["result"] = "❌ Invalid API key"
        write_log(record)
        return jsonify({"error": "Invalid API key"}), 401
    if not x_req_id:
        record["result"] = "❌ Missing X-Request-Id"
        write_log(record)
        return jsonify({"error": "Missing header X-Request-Id"}), 400
    if not body or not isinstance(body, dict):
        record["result"] = "❌ Invalid JSON body"
        write_log(record)
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    name = body.get("name")
    if not name or len(name.strip()) < 2:
        record["result"] = "❌ Invalid name field"
        write_log(record)
        return jsonify({"error": "Invalid 'name' field; must be string length >= 2"}), 400

    # Success
    record["result"] = f"✅ Success for user {name.strip()}"
    write_log(record)

    return jsonify({
        "message": f"Hello, {name.strip()}!",
        "request_id": x_req_id,
        "server_time": int(time.time())
    }), 200


@app.route("/logs/full")
def full_logs():
    """
    Display or download full JSON log file.
    ?download=1 triggers file download.
    """
    if not os.path.exists(LOG_FILE):
        return "No logs found.", 404

    if request.args.get("download"):
        return send_file(LOG_FILE, as_attachment=True, download_name="api-test-results.json")

    with open(LOG_FILE, "r") as f:
        content = f.read()
    return Response(content, mimetype="text/plain")


@app.route("/frontend-log", methods=["POST"])
def frontend_log():
    """
    Optional: Frontend can POST its activity logs manually
    """
    entry = request.get_json(silent=True)
    if not entry:
        return jsonify({"error": "Missing JSON body"}), 400

    entry["source"] = "frontend-event"
    write_log(entry)
    return jsonify({"message": "Frontend log added", "entry": entry})


# -------------------- Main -------------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5090))
    app.run(host="0.0.0.0", port=port)

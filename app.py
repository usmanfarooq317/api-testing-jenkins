# app.py
from flask import Flask, request, jsonify, render_template_string, send_file, Response
import os
import time
import uuid
from datetime import datetime

app = Flask(__name__)

LOG_FILE = "test_results.txt"
REQUEST_LOG = []


def write_log(entry: str):
    """Append logs to test_results.txt with timestamps."""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {entry}\n")


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
    button { padding:8px 16px; cursor:pointer; border:none; border-radius:5px; background:#007bff; color:white; }
    button:hover { background:#0056b3; }
    pre { background:#f7f7f7; padding:12px; border-radius:6px; }
    a.download { text-decoration:none; color:white; background:#28a745; padding:8px 14px; border-radius:5px; margin-left:10px; }
    a.download:hover { background:#1e7e34; }
  </style>
</head>
<body>
  <h1>API Testing Jenkins (port 5090)</h1>

  <div class="card">
    <h3>Call Secure API</h3>
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
    <button onclick="showLogs()">Show recent logs</button>
    <a class="download" href="/logs/full?download=1" target="_blank">⬇ Download Full Log</a>
  </div>

  <div class="card">
    <h3>Full Logs Preview</h3>
    <pre id="fullLogs">Click "Show Logs" to view recent or use "Download Full Log"</pre>
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


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/health")
def health():
    return "OK - port 5090", 200


@app.route("/logs")
def logs():
    return jsonify(REQUEST_LOG[-20:]), 200


@app.route("/logs/full")
def full_logs():
    """
    Endpoint to open or download the full test_results.txt file.
    Query param: ?download=1 triggers download instead of view.
    """
    if not os.path.exists(LOG_FILE):
        return "Log file not found.", 404

    download = request.args.get("download")
    if download:
        return send_file(LOG_FILE, as_attachment=True, download_name="test_results.txt")

    def generate():
        with open(LOG_FILE, "r") as f:
            for line in f:
                yield line
    return Response(generate(), mimetype="text/plain")


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

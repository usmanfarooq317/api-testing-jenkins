# 🧩 Jenkins Pipeline Python Lightweight Project

A single-file **Python Flask project** combining **frontend + backend** on one port (default: `5090`).  
Includes **Jenkins pipeline integration**, **API testing UI**, **logging**, and **EC2 deployment support**.

---

## 🚀 Features

✅ Lightweight Flask app — frontend & backend in one file  
✅ Logs all Jenkins test results and frontend API calls in `test_results.txt`  
✅ View or download logs directly in browser  
✅ Health endpoint and secure API testing with headers  
✅ Works on local machine, Docker, and EC2  
✅ Integrated with Jenkins for CI/CD pipelines  

---

## ⚙️ Project Structure

📂 project-root/
├── app.py # Main Flask app (frontend + backend)
├── test_results.txt # Auto-generated log file (created on first run)
├── Dockerfile # For containerized builds
├── Jenkinsfile # CI/CD pipeline
├── requirements.txt # Flask dependency
└── README.md # Project documentation

yaml
Copy code

---

## 🧠 How It Works

### 🖥️ 1. Frontend (Single Page UI)
The Flask app serves an HTML UI at:

> **http://<server-ip>:5090**

It provides:
- Input fields for API Key, Request ID, and Name
- Buttons to test APIs
- Live response viewer
- Buttons to show logs or download the full log file

---

### 🔒 2. Backend APIs

#### ✅ `/api/secure` (POST)
Used to simulate secure API calls.  
Headers required:
- `X-Api-Key`: must match your secret (default: `secret-key-123`)
- `X-Request-Id`: unique request identifier

Example request body:
<<<<<<< HEAD
json
=======
```json
>>>>>>> e933e3f (logs stored in file)
{
  "name": "Usman"
}
Example response:

json
<<<<<<< HEAD
=======
Copy code
>>>>>>> e933e3f (logs stored in file)
{
  "message": "Hello, Usman!",
  "request_id": "req-123",
  "server_time": 1730898900
}
Logs success or failure into test_results.txt.

🔁 /api/echo (GET/POST)
Echoes back request details for debugging.

❤️ /health
Quick check if the server is running.

📜 /logs/full
Displays the full test log in browser (text preview).
Append ?download=1 to download it directly as test_results.txt.

Example:

View: http://<ec2-public-ip>:5090/logs/full

Download: http://<ec2-public-ip>:5090/logs/full?download=1

🧩 Log System Details
All logs are stored in test_results.txt in the app directory.

Each entry is timestamped, e.g.:

vbnet
<<<<<<< HEAD
=======
Copy code
>>>>>>> e933e3f (logs stored in file)
[2025-11-07 13:55:31] SUCCESS API call by Usman with req_id=req-8a32d2
[2025-11-07 13:55:45] ERROR Invalid API key from 172.31.12.45
Log entries are generated both from:

Jenkins test results

Frontend /api/secure and /api/echo requests

📋 Jenkins Integration
Jenkinsfile Includes:
Checkout stage

Build & Test

Run Flask app on port 5090

Append Jenkins build logs to test_results.txt

Archive logs as Jenkins artifacts

Optionally push Docker image to Docker Hub or deploy to EC2

Example Jenkinsfile log integration:
groovy
Copy code
post {
    always {
        echo "Appending Jenkins build logs to test_results.txt"
        sh '''
          echo "[Jenkins Build Completed: $(date)]" >> test_results.txt
          echo "Build Status: ${currentBuild.currentResult}" >> test_results.txt
          echo "----------------------------------------------" >> test_results.txt
        '''
        archiveArtifacts artifacts: 'test_results.txt', fingerprint: true
    }
}
This ensures your Jenkins console output summary is stored permanently inside the same test_results.txt file viewable from /logs/full.

☁️ EC2 Deployment
1️⃣ SSH into EC2
bash
<<<<<<< HEAD
ssh -i "your-key.pem" ubuntu@<ec2-public-ip>
2️⃣ Clone your repo
bash
=======
Copy code
ssh -i "your-key.pem" ubuntu@<ec2-public-ip>
2️⃣ Clone your repo
bash
Copy code
>>>>>>> e933e3f (logs stored in file)
git clone https://github.com/usmanfarooq317/jenkins-flask-app.git
cd jenkins-flask-app
3️⃣ Install dependencies
bash
<<<<<<< HEAD
=======
Copy code
>>>>>>> e933e3f (logs stored in file)
sudo apt update
sudo apt install python3-pip -y
pip install -r requirements.txt
4️⃣ Run app
bash
<<<<<<< HEAD
=======
Copy code
>>>>>>> e933e3f (logs stored in file)
python3 app.py
5️⃣ Access in browser
http://<ec2-public-ip>:5090

🧾 Logs Access
🔹 In Frontend UI:
Click “Show Logs” to view recent logs directly on the page

Click “⬇ Download Full Log” to download test_results.txt

🔹 In EC2 Terminal:
bash
<<<<<<< HEAD

=======
Copy code
>>>>>>> e933e3f (logs stored in file)
cat test_results.txt
or live follow logs:

bash
<<<<<<< HEAD
=======
Copy code
>>>>>>> e933e3f (logs stored in file)
tail -f test_results.txt
🧪 Testing
Open your browser:

cpp
<<<<<<< HEAD
=======
Copy code
>>>>>>> e933e3f (logs stored in file)
http://<ec2-public-ip>:5090
Enter:

X-Api-Key: secret-key-123

X-Request-Id: req-123

Name: Usman

Click Call /api/secure

Check “Response” panel and verify entry in test_results.txt

🧰 Example Output in Browser
API Response

json
<<<<<<< HEAD
=======
Copy code
>>>>>>> e933e3f (logs stored in file)
HTTP 200
{
  "message": "Hello, Usman!",
  "request_id": "req-8a32d2",
  "server_time": 1730993200
}
Log Entry

csharp
<<<<<<< HEAD
[2025-11-07 13:55:31] SUCCESS API call by Usman with req_id=req-8a32d2
📦 Download Full Logs (direct link)
pgsql
http://<ec2-public-ip>:5090/logs/full?download=1
🧰 Run via Docker (optional)
bash
=======
Copy code
[2025-11-07 13:55:31] SUCCESS API call by Usman with req_id=req-8a32d2
📦 Download Full Logs (direct link)
pgsql
Copy code
http://<ec2-public-ip>:5090/logs/full?download=1
🧰 Run via Docker (optional)
bash
Copy code
>>>>>>> e933e3f (logs stored in file)
docker build -t jenkins-flask-app .
docker run -d -p 5090:5090 jenkins-flask-app
Then access:

<<<<<<< HEAD
http://localhost:5090
=======
http://localhost:5090
>>>>>>> e933e3f (logs stored in file)

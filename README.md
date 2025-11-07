# api-testing-jenkins

Single-file Python Flask app that serves frontend + backend on port 5090.
Includes Dockerfile, curl-based tests, and a Jenkinsfile that demonstrates:
- version generation (v1, v2, v3...)
- building image
- running container for tests
- running API tests (header missing / wrong / bad body)
- pushing to Docker Hub and deploying to EC2 with rollback

## Files
- `app.py` - single-file Flask app + frontend HTML.
- `requirements.txt` - Python dependencies.
- `Dockerfile` - build container exposing port 5090.
- `tests/run_tests.sh` - test script Jenkins will run (curl variants).
- `Jenkinsfile` - full pipeline using credentials `docker-hub` and `usman-ec2-key`.
- `jenkins-job-config.xml` - sample Jenkins job config.
- `README.md` - you’re reading it :)

## Local run (no docker)
1. Create virtualenv and install:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   export SECRET_API_KEY="secret-key-123"
   python app.py

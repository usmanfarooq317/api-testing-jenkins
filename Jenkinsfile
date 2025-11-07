pipeline {
    agent any

    triggers {
        githubPush()
    }

    environment {
        DOCKER_USER = 'usmanfarooq317'                // uses the same credential name you used
        IMAGE_NAME = 'api-testing-jenkins'           // NEW image name (no bvs)
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/usmanfarooq317/api-testing-jenkins.git'
            }
        }

        stage('Generate Version Tag') {
            steps {
                script {
                    // try to fetch existing tags from Docker Hub; fallback to v1
                    def existingTags = sh(
                        script: "set -o pipefail; curl -s https://hub.docker.com/v2/repositories/${DOCKER_USER}/${IMAGE_NAME}/tags/?page_size=100 | jq -r '.results[].name' | grep -E '^v[0-9]+' || true",
                        returnStdout: true
                    ).trim()
                    if (!existingTags) {
                        env.NEW_VERSION = "v1"
                    } else {
                        def numbers = existingTags.readLines().collect { it.replace('v', '').toInteger() }
                        env.NEW_VERSION = "v" + (numbers.max() + 1)
                    }
                    echo "✅ New Version to build: ${env.NEW_VERSION}"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${DOCKER_USER}/${IMAGE_NAME}:latest ."
            }
        }

        stage('Run container for tests') {
            steps {
                script {
                    // run container in background mapping port 5090
                    sh """
                      docker rm -f ${IMAGE_NAME}-local-test || true
                      docker run -d --name ${IMAGE_NAME}-local-test -p 5090:5090 ${DOCKER_USER}/${IMAGE_NAME}:latest
                      # wait for app to be ready
                      echo "Waiting for app to become ready..."
                      for i in \$(seq 1 20); do
                        if curl -sS http://127.0.0.1:5090/health >/dev/null 2>&1; then
                          echo "App ready"
                          break
                        fi
                        sleep 1
                      done
                    """
                }
            }
        }

        stage('Run API Tests (curl variants)') {
            steps {
                // run the test script on the agent (tests prints outputs)
                sh "chmod +x tests/run_tests.sh || true"
                sh "tests/run_tests.sh | tee api-tests-output.txt"
                // archive the file for later inspection
                archiveArtifacts artifacts: 'api-tests-output.txt', fingerprint: true
            }
        }

        stage('Tag & Push to Docker Hub') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASS')]) {
                        sh """
                          echo "$DOCKER_PASS" | docker login -u "$DOCKER_USERNAME" --password-stdin
                          docker tag ${DOCKER_USER}/${IMAGE_NAME}:latest ${DOCKER_USER}/${IMAGE_NAME}:${env.NEW_VERSION}
                          docker push ${DOCKER_USER}/${IMAGE_NAME}:latest
                          docker push ${DOCKER_USER}/${IMAGE_NAME}:${env.NEW_VERSION}
                        """
                    }
                }
            }
        }


        stage('Deploy to EC2') {
            steps {
                script {
                    try {
                        sshagent(['usman-ec2-key']) {
                            // change to your EC2 user@host if required in Jenkins credentials or parametrized
                            sh """
                              ssh -o StrictHostKeyChecking=no ubuntu@YOUR.EC2.IP.ADDRESS '
                                docker pull ${DOCKER_USER}/${IMAGE_NAME}:${env.NEW_VERSION} &&
                                docker stop ${IMAGE_NAME}-service || true &&
                                docker rm ${IMAGE_NAME}-service || true &&
                                docker run -d --name ${IMAGE_NAME}-service -p 5090:5090 ${DOCKER_USER}/${IMAGE_NAME}:${env.NEW_VERSION}
                              '
                            """
                        }
                    } catch (err) {
                        echo "❌ EC2 Deploy Failed! Reverting Docker Tag..."
                        // remove pushed tag from Docker Hub (best-effort)
                        withCredentials([usernamePassword(credentialsId: 'docker-hub', passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USERNAME')]) {
                            sh """
                              curl -X DELETE -u "${DOCKER_USERNAME}:${DOCKER_PASS}" \
                                https://hub.docker.com/v2/repositories/${DOCKER_USER}/${IMAGE_NAME}/tags/${env.NEW_VERSION}/ || true
                            """
                        }
                        sh "docker rmi ${DOCKER_USER}/${IMAGE_NAME}:${env.NEW_VERSION} || true"
                        error("Deployment Failed, tag reverted.")
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ Build, Push & Deploy Successful! Version: ${env.NEW_VERSION}"
        }
        failure {
            echo "❌ Pipeline Failed! See console log and archived test output."
        }
    }
}

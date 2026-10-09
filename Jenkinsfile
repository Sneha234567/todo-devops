pipeline {
    agent any

    triggers {
        // Fallback if webhook isn't set up: check GitHub every minute
        pollSCM('* * * * *')
    }

    environment {
        DOCKER_USER = 'YOUR_DOCKERHUB_USERNAME'
        IMAGE       = "${DOCKER_USER}/todo-app"
        TAG         = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install & Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    pytest -v
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE:$TAG -t $IMAGE:latest .'
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                        usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        echo "$PASS" | docker login -u "$USER" --password-stdin
                        docker push $IMAGE:$TAG
                        docker push $IMAGE:latest
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                    sed -i "s|IMAGE_PLACEHOLDER|$IMAGE:$TAG|g" k8s/deployment.yaml
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml
                    kubectl rollout status deployment/todo-app --timeout=90s
                '''
            }
        }
    }

    post {
        success { echo 'Pipeline finished: app deployed to Kubernetes.' }
        failure { echo 'Pipeline failed. Check the stage logs above.' }
    }
}

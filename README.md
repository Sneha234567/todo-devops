# To-Do App: GitHub + Jenkins + Docker + Kubernetes

A simple Flask To-Do app with a fully automated CI/CD pipeline.

    git push -> GitHub -> Jenkins -> test -> Docker build/push -> Kubernetes deploy

## Run locally
    pip install -r requirements.txt
    python app.py          # http://localhost:5000

## Test
    pytest -v

## Docker
    docker build -t todo-app .
    docker run -d -p 5000:5000 todo-app

## Kubernetes (Minikube)
    kubectl apply -f k8s/
    minikube service todo-service

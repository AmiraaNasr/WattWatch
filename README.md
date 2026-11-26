# Détection d'anomalies de consommation électrique

React (nginx) -> FastAPI -> MySQL, et FastAPI -> service IA (Isolation Forest). Tout est conteneurisé.
Terraform crée l'infra CI/CD locale (Jenkins + registre d'images), Jenkins construit et déploie. Aucun service payant.

## Prérequis (tous gratuits)
Docker (Desktop ou Engine) avec le plugin compose, Terraform, Git, un compte GitHub.

## Lancer l'appli en local (sans Jenkins)
    cp .env.example .env
    docker compose up --build        # http://localhost

## Tests
    cd backend && pip install -r requirements-dev.txt && pytest -q
    cd ai && pip install -r requirements-dev.txt && pytest -q

## Infrastructure CI/CD
    cd terraform && terraform init && terraform apply
    docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
    # Jenkins : http://localhost:8080 ; appli déployée par Jenkins : http://localhost:8081
Voir docs/api-contract.md pour les routes.

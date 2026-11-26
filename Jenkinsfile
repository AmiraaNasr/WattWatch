// Multibranch : tests + build sur toutes les branches ; push registre + deploiement sur main.
// Jenkins tourne dans un conteneur et pilote le Docker de l'hote (docker.sock).
pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '15'))
  }

  triggers { pollSCM('H/2 * * * *') }

  environment {
    REGISTRY            = 'localhost:5000'
    TAG                 = "${env.BUILD_NUMBER}"
    APP_PORT            = '8081'
    // Credentials "Secret text" a creer dans Jenkins (lettres et chiffres uniquement)
    MYSQL_ROOT_PASSWORD = credentials('mysql-root-password')
    MYSQL_PASSWORD      = credentials('mysql-user-password')
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Tests') {
      parallel {
        stage('Backend') {
          steps {
            sh '''
              docker run --rm --volumes-from jenkins -w "$WORKSPACE/backend" python:3.11-slim \
                sh -c "pip install -q -r requirements-dev.txt && pytest -q"
            '''
          }
        }
        stage('IA') {
          steps {
            sh '''
              docker run --rm --volumes-from jenkins -w "$WORKSPACE/ai" python:3.11-slim \
                sh -c "pip install -q -r requirements-dev.txt && pytest -q"
            '''
          }
        }
      }
    }

    stage('Build images') {
      parallel {
        stage('frontend') { steps { sh 'docker build -t $REGISTRY/power-frontend:$TAG -t $REGISTRY/power-frontend:latest ./frontend' } }
        stage('backend')  { steps { sh 'docker build -t $REGISTRY/power-backend:$TAG  -t $REGISTRY/power-backend:latest  ./backend' } }
        stage('ia')       { steps { sh 'docker build -t $REGISTRY/power-ai:$TAG       -t $REGISTRY/power-ai:latest       ./ai' } }
      }
    }

    stage('Push registre') {
      when { branch 'main' }
      steps {
        sh '''
          for svc in frontend backend ai; do
            docker push $REGISTRY/power-$svc:$TAG
            docker push $REGISTRY/power-$svc:latest
          done
        '''
      }
    }

    stage('Deploy') {
      when { branch 'main' }
      steps {
        sh '''
          docker compose -p power pull
          docker compose -p power up -d --remove-orphans
        '''
      }
    }

    stage('Smoke test') {
      when { branch 'main' }
      steps {
        sh '''
          for i in $(seq 1 20); do
            if docker run --rm --network power_default curlimages/curl:8.10.1 -fsS http://frontend/api/health; then
              echo " <- OK (appli sur http://localhost:$APP_PORT)"; exit 0
            fi
            echo "attente de l'application ($i/20)"; sleep 6
          done
          exit 1
        '''
      }
    }
  }

  post {
    success { echo 'Pipeline termine avec succes' }
    failure { echo 'Pipeline en echec : voir les logs de l etape' }
  }
}

pipeline {
    agent any

    environment {
        USE_SQLITE = 'true'
        LLM_PROVIDER = 'mock'
        SELENIUM_BASE_URL = 'http://127.0.0.1:4173'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Backend Setup & Lint') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip
                    .venv/bin/pip install -r requirements.txt
                    .venv/bin/flake8 src/backend/recipes tests/backend --max-line-length=120 --exclude=migrations
                '''
            }
        }

        stage('Backend Unit & Safety Evaluation') {
            steps {
                sh '''
                    .venv/bin/python src/backend/manage.py migrate --noinput
                    .venv/bin/coverage run -m pytest
                    .venv/bin/coverage report -m
                    .venv/bin/coverage xml -o coverage.xml
                    .venv/bin/python tests/evaluate_substitutions.py
                '''
            }
        }

        stage('Frontend Test & Build') {
            steps {
                dir('src/frontend') {
                    sh '''
                        npm ci || npm install
                        npm test
                        npm run build
                    '''
                }
            }
        }

        stage('Selenium E2E Journey') {
            steps {
                sh '''
                    .venv/bin/python src/backend/manage.py seed_data
                    .venv/bin/python src/backend/manage.py runserver 127.0.0.1:8000 &
                    BACK_PID=$!
                    (cd src/frontend && npm run preview -- --port 4173 --host 127.0.0.1) &
                    FRONT_PID=$!
                    sleep 3
                    .venv/bin/pytest tests/selenium/test_user_journey.py || EXIT_CODE=$?
                    kill $BACK_PID $FRONT_PID || true
                    exit ${EXIT_CODE:-0}
                '''
            }
        }

        stage('SonarQube Quality Gate') {
            when {
                expression { return env.SONAR_HOST_URL != null && env.SONAR_HOST_URL != '' }
            }
            steps {
                sh 'sonar-scanner -Dproject.settings=sonar-project.properties'
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker compose build
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'coverage.xml,evidence/phase4/*', allowEmptyArchive: true
        }
    }
}

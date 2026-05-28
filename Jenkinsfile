pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Package directory'
                sh("""
                    cd $WORKSPACE
                    tar cvf saythanks.io.tar *
                """)
            }
        }
        stage('Deploy in Test Server') {
            steps {
                echo 'Deploy package in Test server '
            }
        }
        stage('Run Automation tests') {
            steps {
                echo 'Run Automation Tests'
            }
        }

        stage('Deploy in Production') {
            steps {
                echo 'Deploying changes in Production server'
            }
        }

    }
}

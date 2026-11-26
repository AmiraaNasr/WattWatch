output "jenkins_url" {
  value = "http://localhost:${var.jenkins_port}"
}

output "registry_url" {
  value = "localhost:${var.registry_port}"
}

output "jenkins_initial_password_cmd" {
  value = "docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword"
}

# Infrastructure CI/CD 100 % gratuite et locale : reseau, volumes, registre prive, Jenkins.

resource "docker_network" "cicd" {
  name = "cicd"
}

resource "docker_volume" "jenkins_home" {
  name = "jenkins_home"
}

resource "docker_volume" "registry_data" {
  name = "registry_data"
}

# ---------- Registre d'images prive (remplace Docker Hub) ----------
resource "docker_image" "registry" {
  name         = "registry:2"
  keep_locally = true
}

resource "docker_container" "registry" {
  name    = "registry"
  image   = docker_image.registry.image_id
  restart = "unless-stopped"

  ports {
    internal = 5000
    external = var.registry_port
  }
  volumes {
    volume_name    = docker_volume.registry_data.name
    container_path = "/var/lib/registry"
  }
  networks_advanced {
    name = docker_network.cicd.name
  }
}

# ---------- Jenkins ----------
resource "docker_image" "jenkins" {
  name         = "power-jenkins:latest"
  keep_locally = true
  build {
    context = "${path.module}/jenkins"
  }
  triggers = {
    dockerfile = filemd5("${path.module}/jenkins/Dockerfile")
  }
}

resource "docker_container" "jenkins" {
  name    = "jenkins"
  image   = docker_image.jenkins.image_id
  restart = "unless-stopped"
  user    = "root" # acces a docker.sock (usage pedagogique)

  ports {
    internal = 8080
    external = var.jenkins_port
  }
  volumes {
    volume_name    = docker_volume.jenkins_home.name
    container_path = "/var/jenkins_home"
  }
  volumes {
    host_path      = "/var/run/docker.sock"
    container_path = "/var/run/docker.sock"
  }
  networks_advanced {
    name = docker_network.cicd.name
  }
}

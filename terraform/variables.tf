variable "docker_host" {
  type        = string
  default     = "unix:///var/run/docker.sock"
  description = "Linux/macOS/WSL2 : unix:///var/run/docker.sock ; Windows natif : npipe:////./pipe/docker_engine"
}

variable "jenkins_port" {
  type    = number
  default = 8080
}

variable "registry_port" {
  type    = number
  default = 5000
}

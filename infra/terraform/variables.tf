variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1"   # Mumbai — change as needed
}

variable "project_name" {
  description = "Tag prefix for all resources"
  type        = string
  default     = "prettypleaseapprove"
}

variable "key_pair_name" {
  description = "Name of existing EC2 key pair for SSH access"
  type        = string
}

variable "admin_cidr" {
  description = "Your IP CIDR for SSH access (e.g. 203.0.113.5/32)"
  type        = string
}

variable "jenkins_instance_type" {
  description = "EC2 instance type for Jenkins"
  type        = string
  default     = "t3.medium"   # 2 vCPU / 4 GB — minimum for Jenkins
}

variable "sonarqube_instance_type" {
  description = "EC2 instance type for SonarQube"
  type        = string
  default     = "t3.large"    # 2 vCPU / 8 GB — SonarQube is memory-hungry
}

variable "bot_backend_instance_type" {
  description = "EC2 instance type for bot backend (FastAPI)"
  type        = string
  default     = "t3.small"
}

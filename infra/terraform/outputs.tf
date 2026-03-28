output "jenkins_public_ip" {
  description = "Jenkins public IP — open :8080 in browser after setup"
  value       = aws_eip.jenkins.public_ip
}

output "jenkins_url" {
  description = "Jenkins web UI URL"
  value       = "http://${aws_eip.jenkins.public_ip}:8080"
}

output "sonarqube_private_ip" {
  description = "SonarQube private IP (VPC-internal; Jenkins connects here)"
  value       = aws_instance.sonarqube.private_ip
}

output "sonarqube_url" {
  description = "SonarQube URL (accessible from within VPC)"
  value       = "http://${aws_instance.sonarqube.private_ip}:9000"
}

output "bot_backend_public_ip" {
  description = "Bot backend public IP — point GitHub webhook here"
  value       = aws_eip.bot_backend.public_ip
}

output "bot_backend_webhook_url" {
  description = "GitHub webhook URL to configure in repo settings"
  value       = "http://${aws_eip.bot_backend.public_ip}:8000/api/v1/webhook/github"
}

output "ansible_inventory_hint" {
  description = "Paste these IPs into infra/ansible/inventory.ini"
  value = <<-EOT
    [jenkins]
    ${aws_eip.jenkins.public_ip}

    [sonarqube]
    ${aws_instance.sonarqube.private_ip}

    [bot_backend]
    ${aws_eip.bot_backend.public_ip}
  EOT
}

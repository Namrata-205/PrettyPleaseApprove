# ============================================================
# prettypleaseapprove — Infrastructure (Terraform)
# Provisions: 1x Jenkins VM, 1x SonarQube VM, 1x Bot Backend VM
# Provider: AWS (swap provider block for GCP/Azure as needed)
# ============================================================

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to store state remotely (recommended for teams)
  # backend "s3" {
  #   bucket  = "your-tfstate-bucket"
  #   key     = "pr-review-bot/terraform.tfstate"
  #   region  = var.aws_region
  #   encrypt = true
  # }
}

provider "aws" {
  region = var.aws_region
}

# ── DATA: Fetch latest Ubuntu 22.04 AMI ──────────────────────
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# ── VPC / NETWORKING ─────────────────────────────────────────
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "${var.project_name}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project_name}-igw" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.project_name}-public-subnet" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "${var.project_name}-rt" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ── SECURITY GROUPS ──────────────────────────────────────────

# Jenkins SG: 8080 (UI), 50000 (agent JNLP), SSH from your IP
resource "aws_security_group" "jenkins" {
  name   = "${var.project_name}-jenkins-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    description = "Jenkins web UI"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Jenkins agent"
    from_port   = 50000
    to_port     = 50000
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${var.project_name}-jenkins-sg" }
}

# SonarQube SG: 9000 (UI/API), SSH internal only
resource "aws_security_group" "sonarqube" {
  name   = "${var.project_name}-sonarqube-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    description = "SonarQube API + UI"
    from_port   = 9000
    to_port     = 9000
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${var.project_name}-sonarqube-sg" }
}

# Bot backend SG: 8000 (FastAPI), SSH internal + admin
resource "aws_security_group" "bot_backend" {
  name   = "${var.project_name}-bot-backend-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    description = "Bot backend API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block, "0.0.0.0/0"] # expose publicly for GitHub webhooks
  }
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${var.project_name}-bot-backend-sg" }
}

# ── EC2 INSTANCES ─────────────────────────────────────────────

resource "aws_instance" "jenkins" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.jenkins_instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.jenkins.id]
  key_name               = var.key_pair_name

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    apt-get update && apt-get install -y python3 python3-pip
  EOF

  tags = {
    Name    = "${var.project_name}-jenkins"
    Role    = "jenkins"
    Project = var.project_name
  }
}

resource "aws_instance" "sonarqube" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.sonarqube_instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.sonarqube.id]
  key_name               = var.key_pair_name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name    = "${var.project_name}-sonarqube"
    Role    = "sonarqube"
    Project = var.project_name
  }
}

resource "aws_instance" "bot_backend" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.bot_backend_instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.bot_backend.id]
  key_name               = var.key_pair_name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name    = "${var.project_name}-bot-backend"
    Role    = "bot-backend"
    Project = var.project_name
  }
}

# ── ELASTIC IPs (stable public IPs) ──────────────────────────

resource "aws_eip" "jenkins" {
  instance = aws_instance.jenkins.id
  domain   = "vpc"
  tags     = { Name = "${var.project_name}-jenkins-eip" }
}

resource "aws_eip" "bot_backend" {
  instance = aws_instance.bot_backend.id
  domain   = "vpc"
  tags     = { Name = "${var.project_name}-bot-eip" }
}

variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "ap-south-1"
}

variable "aws_profile" {
  description = "AWS CLI authentication profile"
  type        = string
  default     = "terraform"
}

variable "project_name" {
  description = "Project resource naming"
  type        = string
  default     = "edurankai-devops"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ssh_public_key_path" {
  description = "Local SSH public key path"
  type        = string
  default     = "~/.ssh/edurankai_devops.pub"
}

variable "allowed_ssh_cidr" {
  description = "Public IP allowed to access SSH"
  type        = string
  default     = "103.103.56.210/32"
}

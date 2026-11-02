output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "instance_public_ip" {
  description = "Public IP of EC2 instance"
  value       = aws_instance.app.public_ip
}

output "instance_public_dns" {
  description = "Public DNS of EC2 instance"
  value       = aws_instance.app.public_dns
}

output "ubuntu_ami_id" {
  description = "Selected Ubuntu AMI"
  value       = data.aws_ami.ubuntu.id
}

output "security_group_id" {
  description = "Application security group ID"
  value       = aws_security_group.app.id
}

output "subnet_id" {
  description = "Selected AWS subnet"
  value       = aws_instance.app.subnet_id
}

provider "aws" {
  region = "us-east-1"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

data "aws_eip" "harbor_eip" {
  public_ip = "3.226.105.11"
}
resource "aws_instance" "worker" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_k8s
  count         = 2
  key_name      = "registry"
  # Confite Root Volume
  root_block_device {
    volume_size           = 10
    volume_type           = "gp3"
    delete_on_termination = true
  }
  # Configure Subnet and Security Group
  subnet_id       = aws_subnet.k8s_public_subnet.id
  security_groups = [aws_security_group.k8s_security_group.id]
  # Configure Public IP
  associate_public_ip_address = true
  # Configure Tags
  tags = {

    Name = "${var.instance_worker}-${count.index}"
  }
}

resource "aws_instance" "master" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_k8s
  count         = 1
  # Configure Subnet and Security Group
  subnet_id       = aws_subnet.k8s_public_subnet.id
  security_groups = [aws_security_group.k8s_security_group.id]
  # Configure Public IP
  associate_public_ip_address = true
  key_name                    = "registry"
  # Configure Root Volume
  root_block_device {
    volume_size           = 10
    volume_type           = "gp3"
    delete_on_termination = true
  }
  tags = {
    Name = var.instance_master
  }
}

resource "aws_instance" "harbor" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_harbor
  # Configure Subnet and Security Group
  subnet_id       = aws_subnet.k8s_public_subnet.id
  security_groups = [aws_security_group.k8s_security_group.id]
  # Configure Public IP
  associate_public_ip_address = true
  key_name                    = "registry"
  # Configure Root Volume
  root_block_device {
    volume_size           = 10
    volume_type           = "gp3"
    delete_on_termination = true
  }
  user_data = base64encode(file("files/harbor.sh"))
  tags = {
    Name = "harbor"
  }
}

resource "aws_eip_association" "harbor_eip" {
  instance_id   = aws_instance.harbor.id
  allocation_id = data.aws_eip.harbor_eip.id
}

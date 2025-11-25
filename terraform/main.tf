provider "aws" {
  region = "us-east-1"
}

data "aws_ami" "ubuntu" {
    most_recent = true
    owners = ["099720109477"]
    filter {
        name = "name"
        values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
    }

    filter {
        name= "virtualization-type"
        values = ["hvm"]
    }

    filter {
        name = "architecture"
        values = ["x86_64"]
    }
}

resource "aws_instance" "worker"{
    ami = data.aws_ami.ubuntu.id
    instance_type = var.instance_k8s
    count = 2
    # Confite Root Volume
    root_block_device {
      volume_size = 10
      volume_type = "gp3"
      delete_on_termination = true
    }
    # Configure Subnet and Security Group
    subnet_id = aws_subnet.k8s_public_subnet.id
    security_groups = [aws_security_group.k8s_security_group.id]
    # Configure Public IP
    associate_public_ip_address = true
    # Configure Tags
    tags = {

        Name = "${var.instance_worker}-${count.index}"
    }
}

resource "aws_instance" "master" {
    ami = data.aws_ami.ubuntu.id
    instance_type = var.instance_k8s
    count = 1 
    # Configure Subnet and Security Group
    subnet_id = aws_subnet.k8s_public_subnet.id
    security_groups = [aws_security_group.k8s_security_group.id]
    # Configure Public IP
    associate_public_ip_address = true
    # Configure Root Volume
    root_block_device {
        volume_size = 10
        volume_type = "gp3"
        delete_on_termination = true
        } 
    tags = {
        Name = var.instance_master
    }
}

resource "aws_instance" "harbor" {
    ami =data.aws_ami.ubuntu.id
    instance_type = var.instance_harbor
    count = 1 
    # Configure Subnet and Security Group
    subnet_id = aws_subnet.k8s_public_subnet.id
    security_groups = [aws_security_group.k8s_security_group.id]
    # Configure Public IP
    associate_public_ip_address = true
    # Configure Root Volume
    root_block_device {
        volume_size = 10
        volume_type = "gp3"
        delete_on_termination = true
        } 
    tags ={
        Name = "harbor"
    }   
}


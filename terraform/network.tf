# Create VPC
resource "aws_vpc" "k8s_vpc" {
    cidr_block = "10.0.0.0/16"
    enable_dns_hostnames = true
    enable_dns_support = true
    tags = {
        Name = "k8s_vpc"
    }
}

# Create Internet Gateway
resource "aws_internet_gateway" "k8s_igw"{
    vpc_id = aws_vpc.k8s_vpc.id
    tags = {
        Name = "k8s_igw"
    }
}

# Create Public Subnet
resource "aws_subnet" "k8s_public_subnet"{
    vpc_id = aws_vpc.k8s_vpc.id
    cidr_block = "10.0.1.0/24"
    availability_zone = "us-east-1a"
    tags = {
        Name = "k8s_public_subnet"
    }
}

#Create Route Table
resource "aws_route_table" "k8s_public_rt"{
    vpc_id = aws_vpc.k8s_vpc.id
    route  {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_internet_gateway.k8s_igw.id
    }
    tags = {
        Name = "k8s_public_rt"
    }
}

# Create Public Subnet Association
resource "aws_route_table_association" "k8s_public_rt_assoc"{
    subnet_id = aws_subnet.k8s_public_subnet.id
    route_table_id = aws_route_table.k8s_public_rt.id
}

# Create Security Group
resource "aws_security_group" "k8s_security_group" {
    name = "k8s_security_group"
    description = "Security group for k8s"
    vpc_id = aws_vpc.k8s_vpc.id

    ingress {
        description = "SSH traffic"
        from_port = 0
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        description = "HTTP traffic"
        from_port = 0
        to_port = 80
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        description = "HTTPS traffic"
        from_port = 0
        to_port = 443
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}

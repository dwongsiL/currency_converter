variable "instance_worker" {
  description = "Value of the EC2 instance's Name tag"
  type = string
  default = "k8-worker"
}
variable "instance_master" {
    description = "Value of the EC2 instance's Name tag"
    type = string
    default = "k8-master"
}

variable "instance_harbor" {
    description = "Type of the EC2 instance"
    type = string
    default = "t3.micro"
}
variable "instance_k8s"{
    description = "Type of the EC2 instance"
    type = string
    default = "c7i-flex.large"
}

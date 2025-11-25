#!/bin/bash

# Update packages
sudo apt update && sudo apt upgrade -y

# Install packages dependencies
sudo apt -y install curl apt-transport-https vim git wget gnupg2 software-properties-common ca-certificates

# Install kubelet, kubeadm, kubectl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt update
sudo apt install -y kubelet kubeadm kubectl

# Hold version of kubelet, kubeadm and kubectl
sudo apt-mark hold kubelet kubeadm kubectl

# Disable swap
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
sudo swapoff -a
sudo mount -a

sudo modprobe overlay
sudo modprobe br_netfilter

# Configure sysctl
sudo tee /etc/sysctl.d/kubernetes.conf <<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF

sudo sysctl --system

# Install containerd
# Add modules to /etc/modules-load.d/
sudo tee /etc/modules-load.d/containerd.conf <<EOF
overlay
br_netfilter
EOF
# Load modules
sudo modprobe overlay
sudo modprobe br_netfilter

# Add docker repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

sudo apt update
sudo apt install -y containerd.io

# Configure containerd
sudo su -
mkdir -p /etc/containerd
containerd config default >/etc/containerd/config.toml
sudo systemctl restart containerd
sudo systemctl enable containerd
systemctl status containerd

kubeadm join 192.168.12.13:6443 --token 28tobh.qjp2ib31yr6cekzi --discovery-token-ca-cert-hash sha256:cb9cf4668ffd694c2a29dae9bf6996b88d8db981e05b4de824a4c0187d01a51c

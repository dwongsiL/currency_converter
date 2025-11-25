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

# Install master node
lsmod | grep br_netfilter
sudo systemctl enable kubelet
sudo kubeadm config images pull

sudo kubeadm init \
	--pod-network-cidr=192.168.0.0/16 \
	--cri-socket unix:///run/containerd/containerd.sock \
	--apiserver-advertise-address=192.168.12.13

mkdir -p $HOME/.kube
sudo cp -f /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

kubectl cluster-info

kubectl create -f https://docs.projectcalico.org/manifests/tigera-operator.yaml
kubectl create -f https://docs.projectcalico.org/manifests/custom-resources.yaml

kubectl taint nodes --all node-role.kubernetes.io/control-plane-

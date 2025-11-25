#!/bin/bash

#Update packages
sudo apt update && sudo apt upgrade -y

# Install Packages Dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
	"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

sudo apt update -y

# Install Docker Engine
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Enable Docker Service
sudo systemctl is-enabled docker
sudo systemctl start docker

# Add User to Docker Group
sudo usermod -aG docker $USER
# Install cerbot
sudo apt install certbot -y

# Certbot
sudo certbot certonly --standalone -d registry.dwong.space -m leobridget6@gmai.com --agree-tos --preferred-challenges http --keep-until-expiring

# Install Harbor
cd /opt
curl -s https://api.github.com/repos/goharbor/harbor/releases/latest | grep browser_download_url | cut -d '"' -f 4 | grep '\.tgz$' | wget -i -
tar xvf harbor-offline-installer-*.tgz

# Configure HarBor
cd /opt/harbor

cp harbor.yml.tmpl harbor.yml

# Edit harbor.yml

sed -i 's/^hostname: .*/hostname: registry.dwong.space/' harbor.yml

sed -i \
	-e "s|^\(\s*certificate:\s*\).*|\1/etc/letsencrypt/live/registry.dwong.space/fullchain.pem|" \
	-e "s|^\(\s*private_key:\s*\).*|\1/etc/letsencrypt/live/registry.dwong.space/privkey.pem|" \
	harbor.yml

# Run prepare
sudo ./prepare
# Run install
sudo ./install.sh

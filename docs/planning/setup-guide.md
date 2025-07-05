# PromptCraft-Hybrid: Server Setup & Onboarding Guide

Version: 1.0
Audience: Operations Team, DevOps Engineers
Purpose: This document provides the complete step-by-step process for provisioning a new server and deploying the Phase 1 PromptCraft-Hybrid application stack.

## 1\. Overview

This guide covers two main stages:

1. **Server Provisioning:** Preparing a base Ubuntu Server with all necessary system-level dependencies.
2. **Application Bootstrap:** Cloning the application repository and using a bootstrap script to configure the environment and launch the application via Docker Compose.

The goal is to create a repeatable, scripted process that ensures a consistent deployment environment.

## 2\. Server Provisioning

### 2.1. Prerequisites

* **Hardware:** A server (virtual or physical) meeting the minimum specs:
  * **OS:** Ubuntu Server 22.04 LTS
  * **CPU:** 8+ Cores
  * **RAM:** 32GB+ (256GB recommended for full production)
  * **Storage:** 512GB+ NVMe SSD
* **Access:** SSH access with sudo privileges.

### 2.2. Step-by-Step Provisioning

These commands should be run on the newly provisioned Ubuntu server.

#### Step 1: System Update

Ensure all system packages are up to date.

sudo apt-get update && sudo apt-get upgrade \-y

#### Step 2: Install Core Dependencies

Install essential packages like Git and tools needed for Docker's repository.

sudo apt-get install \-y git curl apt-transport-https ca-certificates gnupg-agent software-properties-common

#### Step 3: Install Docker Engine

Follow the official Docker installation steps.

\# Add Docker's official GPG key
sudo install \-m 0755 \-d /etc/apt/keyrings
curl \-fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg \--dearmor \-o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

\# Set up the Docker repository
echo \\
  "deb \[arch=$(dpkg \--print-architecture) signed-by=/etc/apt/keyrings/docker.gpg\] https://download.docker.com/linux/ubuntu \\
  $(. /etc/os-release && echo "$VERSION\_CODENAME") stable" | \\
  sudo tee /etc/apt/sources.list.d/docker.list \> /dev/null

\# Install Docker Engine and Compose
sudo apt-get update
sudo apt-get install \-y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

#### Step 4: Configure Docker Post-Installation

Add the current user to the docker group to run Docker commands without sudo.

\# Replace ${USER} with the appropriate username if not the current user
sudo usermod \-aG docker ${USER}

\# You will need to log out and log back in for this change to take effect.
echo "Please log out and log back in to apply Docker group permissions."

Verify the installation by running docker \--version and docker compose version.

## 3\. Application Bootstrap

### 3.1. Overview

The following bootstrap.sh script automates the entire application setup process. It will:

1. Clone the application repository.
2. Copy the example environment file.
3. Launch the application using Docker Compose.

**Note:** This deployment expects an external Qdrant instance at 192.168.1.16:6333 (deployed separately on Unraid).

### 3.2. The Bootstrap Script (bootstrap.sh)

Create a file named bootstrap.sh on the server and paste the following content.

\#\!/bin/bash

\# Exit immediately if a command exits with a non-zero status.
set \-e

\# \--- Configuration \---
\# The Git repository URL for the application
REPO\_URL="https://github.com/your-org/PromptCraft-Hybrid.git"
\# The directory where the application will be cloned
APP\_DIR="/opt/promptcraft-hybrid"
\# External Qdrant connection details
QDRANT\_HOST="192.168.1.16"
QDRANT\_PORT="6333"

echo "--- Starting PromptCraft-Hybrid Application Bootstrap \---"

\# \--- Step 1: Clone Application Repository \---
if \[ \-d "$APP\_DIR" \]; then
    echo "Application directory $APP\_DIR already exists. Skipping clone."
else
    echo "Cloning repository from $REPO\_URL to $APP\_DIR..."
    sudo git clone "$REPO\_URL" "$APP\_DIR"
    sudo chown \-R ${USER}:${USER} "$APP\_DIR"
fi
cd "$APP\_DIR"

\# \--- Step 2: Verify External Qdrant Connection \---
echo "Verifying connection to external Qdrant instance at $QDRANT\_HOST:$QDRANT\_PORT..."
if curl \-f \-s "http://$QDRANT\_HOST:$QDRANT\_PORT/health" \> /dev/null; then
    echo "✓ External Qdrant instance is accessible"
else
    echo "✗ Cannot connect to external Qdrant at $QDRANT\_HOST:$QDRANT\_PORT"
    echo "Please ensure Qdrant is running on Unraid before proceeding."
    exit 1
fi

\# \--- Step 3: Configure Environment \---
if \[ \-f ".env" \]; then
    echo ".env file already exists. Skipping creation."
else
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "IMPORTANT: .env file created. Please edit it now to add your required API keys and secrets."
    \# Pause the script to allow for editing
    read \-p "Press \[Enter\] key to continue after editing .env file..."
fi

\# \--- Step 4: Launch Application Stack \---
echo "Building and launching application containers with Docker Compose..."
docker compose up \--build \-d

echo "--- Bootstrap Complete\! \---"
echo "Application services are starting in the background."
echo "Run 'docker compose ps' to check the status of the containers."
echo "Run 'docker compose logs \-f' to view application logs."

### 3.3. Running the Script

1. Save the script above as bootstrap.sh.
2. Make the script executable:
   chmod \+x bootstrap.sh

3. Run the script:
   ./bootstrap.sh

The script will pause after creating the .env file, allowing the operator to securely add the necessary API keys (ANTHROPIC\_API\_KEY, etc.). Once the operator presses Enter, the script will proceed to launch the full application stack.

This completes the server setup and application deployment process.

## Prerequisites

**External Dependencies:**
- Qdrant vector database running on Unraid at 192.168.1.16:6333
- Ensure the Qdrant instance is accessible from the Ubuntu VM at 192.168.1.205

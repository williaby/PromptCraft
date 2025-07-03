FROM node:22.17.0-bullseye
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y curl apt-transport-https lsb-release gnupg python3 python3-pip git \
 && rm -rf /var/lib/apt/lists/*

# Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Bicep CLI + ensure in PATH
RUN az bicep install \
 && ln -s "$(az bicep where)" /usr/local/bin/bicep

# Functions Core Tools
RUN npm install -g azure-functions-core-tools@4 --unsafe-perm

# Azurite (Storage emulator)
RUN npm install -g azurite

# pre-commit
RUN pip3 install --no-cache-dir pre-commit

WORKDIR /workspace

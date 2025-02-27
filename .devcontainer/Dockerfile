FROM mcr.microsoft.com/vscode/devcontainers/miniconda:0-3

# Install any additional dependencies here
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs

# Copy the environment.yml file to the container
COPY environment.yml /tmp/environment.yml

# Create the Conda environment
RUN conda env create -f /tmp/environment.yml

# Activate the Conda environment
RUN echo "conda activate bitcoin-tx" >> ~/.bashrc

# Copy package.json and package-lock.json to the container
COPY frontend/package.json /workspaces/BitcoinTX_FastPython/frontend/package.json
COPY frontend/package-lock.json /workspaces/BitcoinTX_FastPython/frontend/package-lock.json

# Install frontend dependencies
RUN cd /workspaces/BitcoinTX_FastPython/frontend && npm install
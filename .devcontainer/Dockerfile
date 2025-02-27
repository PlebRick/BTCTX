# Use the VS Code miniconda base image
FROM mcr.microsoft.com/vscode/devcontainers/miniconda:0-3

# 1) Install essential packages
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# 2) Install Node.js 16.x
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs

# 3) Copy the Conda environment.yml into /tmp
COPY environment.yml /tmp/environment.yml

# 4) Create the Conda environment named "bitcoin-tx"
RUN conda env create -f /tmp/environment.yml

# 5) Activate it by default for all bash sessions
#    and also add it to the PATH so non-interactive shells (e.g. build commands) see it
RUN echo "conda activate bitcoin-tx" >> /root/.bashrc
ENV PATH /opt/conda/envs/bitcoin-tx/bin:$PATH

# 6) Copy over your frontend's package files
#    Adjust paths to match your repo's layout
COPY frontend/package.json /workspaces/BitcoinTX_FastPython/frontend/
COPY frontend/package-lock.json /workspaces/BitcoinTX_FastPython/frontend/

# 7) Install npm dependencies
RUN cd /workspaces/BitcoinTX_FastPython/frontend && npm install

# 8) Set the container's working directory to the project
WORKDIR /workspaces/BitcoinTX_FastPython

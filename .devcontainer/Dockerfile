# Base image: Miniconda with Python 3 (ensures conda is available)
FROM mcr.microsoft.com/devcontainers/miniconda:0-3

# [Optional] If the base doesn't default to Python 3.11, ensure it:
# RUN conda install -y python=3.11

# Install Node.js 18 (using NodeSource or devcontainer feature)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get update && apt-get install -y nodejs && \
    npm install -g npm@latest

# Create Conda environment for the project
RUN conda init bash && conda create -y -n btctx python=3.11 

# Activate env by default in any new bash session
ENV PATH="/opt/conda/envs/btctx/bin:${PATH}"
RUN echo "source /usr/local/etc/profile.d/conda.sh && conda activate btctx" >> /etc/bash.bashrc

# Install Python dependencies (in conda env)
COPY backend/requirements.txt /tmp/requirements.txt
RUN bash -c "source /usr/local/etc/profile.d/conda.sh && conda activate btctx && \
    pip install --no-cache-dir -r /tmp/requirements.txt"

# [Optional] Install any OS packages you might need (if any, e.g. git, curl, etc.)
# RUN apt-get install -y <package-name>

# Set working directory
WORKDIR /workspace

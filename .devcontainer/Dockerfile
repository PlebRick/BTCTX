FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Node.js for frontend development
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

# Set up Conda
RUN bash -c "source /usr/local/etc/profile.d/conda.sh && conda init bash && conda create -n btctx python=3.11 -y"

# Activate Conda environment
SHELL ["/bin/bash", "-c"]
RUN echo "conda activate btctx" >> ~/.bashrc

# Set working directory
WORKDIR /workspace

# Install Python dependencies
COPY backend/requirements.txt /workspace/backend/
RUN bash -c "source /usr/local/etc/profile.d/conda.sh && conda activate btctx && pip install --no-cache-dir -r /workspace/backend/requirements.txt"

# Install frontend dependencies
WORKDIR /workspace/frontend
COPY frontend/package.json frontend/package-lock.json /workspace/frontend/
RUN npm install

# Set back to root workspace
WORKDIR /workspace

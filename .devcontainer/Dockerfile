# Use Microsoft's Python Dev Container as the base image
FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Node.js for frontend development
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

# Install Conda and set up a virtual environment
RUN bash -c "source /usr/local/etc/profile.d/conda.sh && conda init bash && conda create -n btctx python=3.11 -y"

# Ensure Conda environment is available in PATH
ENV PATH="/opt/conda/envs/btctx/bin:$PATH"

# Activate Conda automatically for new shell sessions
RUN echo "source /usr/local/etc/profile.d/conda.sh && conda activate btctx" >> ~/.bashrc

# Set working directory to /workspace
WORKDIR /workspace

# Install Python dependencies using Conda environment
COPY backend/requirements.txt /workspace/backend/
RUN bash -c "source /usr/local/etc/profile.d/conda.sh && conda activate btctx && pip install --no-cache-dir -r /workspace/backend/requirements.txt"

# Install frontend dependencies
WORKDIR /workspace/frontend
COPY frontend/package.json frontend/package-lock.json /workspace/frontend/
RUN npm install

# Set back to root workspace
WORKDIR /workspace

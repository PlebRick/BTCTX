#!/bin/bash

# Activate Conda environment
source /usr/local/etc/profile.d/conda.sh
conda activate btctx

# Start the backend server
cd /workspace/backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &

# Start the frontend server
cd /workspace/frontend
npm run dev

To create a tree without unneccesarry files run:

tree -I 'node_modules|__pycache__|*.log|*.pyc|*.pyo|*.pyd|*.env|*.venv|env|venv|ENV|env.bak|venv.bak|dist|dist-ssr|*.local|*.suo|*.ntvs*|*.njsproj|*.sln|*.sw?|Thumbs.db|ehthumbs.db|Desktop.ini|$RECYCLE.BIN|*.iml|*.ipr|*.iws|.idea|.DS_Store|.vscode|logs|htmlcov|pytest_cache|.tox|public/build|migrations|backend/create_db.py'

Start backend server
uvicorn backend.main:app --reload

Start frontend
npm run dev

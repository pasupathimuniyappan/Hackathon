## Create virtual environment
python -m venv venv

## Activate virtual environment
### On macOS/Linux:
source venv/bin/activate

### On Windows:
cd venv\Scripts\activate

## Upgrade pip
pip install --upgrade pip setuptools wheel

## Install core dependencies
pip install -r requirements.txt

## Install development dependencies
pip install -r requirements-dev.txt

## Download spaCy model
python -m spacy download en_core_web_sm

(or)

pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

## Add API Key
Ensure you have added the openai api key in .env

## Run FastAPI server
uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload --log-level debug

## Run MCP Server in separate terminal
source venv/bin/activate
python src/mcp_server.py

## Open API docs
open http://localhost:8000/docs to verify and test the apis

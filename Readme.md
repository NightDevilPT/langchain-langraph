Here's the updated README.md:

```markdown
# LangChain Agents with Docker Model Runner

## Commands

```bash
python run.py              # Show help
python run.py setup        # Setup environment (auto-opens venv terminal)
python run.py list         # List all agents  
python run.py venv         # Open new terminal with venv activated
python run.py quick_agent  # Run an agent
```

## Setup

1. Pull a model:
```bash
docker model pull ai/qwen2.5
```

2. Setup project:
```bash
python run.py setup
```
*This automatically opens a new terminal with virtual environment activated*

3. Copy `.env.example` to `.env` and edit it

4. Or manually activate venv anytime:
```bash
python run.py venv         # Opens new terminal with venv
# OR
.venv\Scripts\activate     # Manual activation (Windows)
source .venv/bin/activate  # Manual activation (Mac/Linux)
```

## Project Structure

```
langchain-langraph/
├── run.py
├── requirements.txt  
├── .env
├── shared/
│   ├── config.py
│   └── llm.py
└── agents/
    └── quick_agent/
        ├── agent.py
        └── tools/
            └── get_weather.py
```

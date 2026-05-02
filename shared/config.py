# shared/config.py
import os
from dotenv import load_dotenv

load_dotenv()

DOCKER_MODEL_RUNNER_URL = os.getenv("DOCKER_MODEL_RUNNER_URL", "http://localhost:12434/engines/v1")
DOCKER_MODEL = os.getenv("DOCKER_MODEL", "ai/qwen2.5")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
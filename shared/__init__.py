# shared/__init__.py
from .config import DOCKER_MODEL_RUNNER_URL, DOCKER_MODEL, MODEL_TEMPERATURE
from .llm import get_llm

__all__ = ["get_llm", "DOCKER_MODEL_RUNNER_URL", "DOCKER_MODEL", "MODEL_TEMPERATURE"]
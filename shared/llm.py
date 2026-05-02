# shared/llm.py
from langchain_openai import ChatOpenAI
from shared.config import DOCKER_MODEL_RUNNER_URL, DOCKER_MODEL, MODEL_TEMPERATURE

def get_llm():
    return ChatOpenAI(
        base_url=DOCKER_MODEL_RUNNER_URL,
        api_key="dummy",
        model=DOCKER_MODEL,
        temperature=MODEL_TEMPERATURE,
    )
# LLM配置

import os
from langchain.chat_models import init_chat_model

ChatModel = init_chat_model(
    openai_api_key=os.environ.get('OPENAI_API_KEY'),
    openai_api_base=os.environ.get('OPENAI_API_BASE'),
    model_provider=os.environ.get('MODEL_PROVIDER'),
    model=os.environ.get('MODEL'),
    temperature=0,
)
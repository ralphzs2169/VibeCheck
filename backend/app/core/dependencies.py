from fastapi import Request
from backend.app.core.model_registry import ModelRegistry


def get_models(request: Request) -> ModelRegistry:
    return request.app.state.models
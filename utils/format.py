from pydantic import BaseModel


def safe_dump(obj) -> dict | str:
    return obj.model_dump() if isinstance(obj, BaseModel) else ""
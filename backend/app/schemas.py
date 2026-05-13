from typing import Literal, Optional

from pydantic import BaseModel, Field


class BuildRequest(BaseModel):
    instruction: str
    project_name: Optional[str] = "Default Project"


class ProjectCreate(BaseModel):
    name: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    project_name: Optional[str] = "Default Project"
    worker_mode: Literal["local", "codex"] = "local"


class CodexTaskRequest(BaseModel):
    message: str = Field(min_length=1)
    project_name: Optional[str] = "Default Project"
    worker_mode: Literal["codex"] = "codex"

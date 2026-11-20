from dataclasses import dataclass
from typing import Literal, Annotated
from pydantic import BaseModel, StringConstraints
import uuid, time

@dataclass(frozen=True)
class SearchPlanningPolicy:
    max_search_queries: int
    max_token_output: int = 2048
    max_planner_calls: int = 1
    
class ChatRequest(BaseModel):
    user_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
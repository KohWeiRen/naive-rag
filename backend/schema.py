from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class SearchPlanningPolicy:
    max_search_queries: int
    token_limit: int
    oversize_output: Literal["split", "clarify"]
    max_planner_calls: int = 1,
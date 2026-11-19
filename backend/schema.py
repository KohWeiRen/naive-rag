from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class SearchPlanningPolicy:
    max_search_queries: int
    max_token_output: int = 2048
    max_planner_calls: int = 1
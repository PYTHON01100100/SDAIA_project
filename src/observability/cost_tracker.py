import logging
from dataclasses import dataclass, field
import litellm
# from litellm import completion_cost

logger = logging.getLogger(__name__)

@dataclass
class StepCost:
    step_number: int
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    is_tool_call: bool = False

@dataclass
class QueryCost:
    query: str
    steps: list[StepCost] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    def add_step(self, step: StepCost):
        self.steps.append(step)
        self.total_cost_usd += step.cost_usd
        self.total_input_tokens += step.input_tokens
        self.total_output_tokens += step.output_tokens

class CostTracker:
    """
    Tracks costs across agent executions.
    """
    def __init__(self):
        self.queries: list[QueryCost] = []
        self._current_query: QueryCost | None = None

    def start_query(self, query: str):
        self._current_query = QueryCost(query=query)
    
    def add_cost(self, cost: float):
        """Add cost manually (used by Agent)."""
        if self._current_query:
            self._current_query.total_cost_usd += cost
        else:
            self.start_query("unknown_query")
            self._current_query.total_cost_usd += cost 
            
    def get_total_cost(self) -> float:
        """Get current total cost (used by Agent)."""
        if self._current_query:
            return self._current_query.total_cost_usd
        return 0.0         

    def log_completion(self, step_number: int, response, is_tool_call: bool = False):
        """
        Log a completion response's cost.
        """
        # TODO: Implement this method
        # 1. Check if _current_query exists
        # 2. Extract usage stats from response
        # 3. Calculate cost (use litellm.completion_cost or fallback)
        # 4. create StepCost and add to query
        if self._current_query is None:
            return
        usage = getattr(response, 'usage', None)
        if usage is None:
            return  
        input_tokens = getattr(usage, 'prompt_tokens', 0)
        output_tokens = getattr(usage, 'completion_tokens', 0) 
        cost = litellm.completion_cost(input_tokens, output_tokens)
        step_cost = StepCost(step_number=step_number,
        model=getattr(response, "model", "unknown"),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        is_tool_call=is_tool_call)
        self._current_query.add_step_cost(step_cost)

    def end_query(self):
        if self._current_query:
            self.queries.append(self._current_query)
            self._current_query = None

    def print_cost_breakdown(self):
        # TODO: Print detailed cost breakdown
        if self._current_query is None:
            print("No active query to display cost breakdown.")
            return
        if not self._current_query.step_costs:
            print("No cost data available.")
            return
        total_cost = 0
        total_input_tokens = 0
        total_output_tokens = 0
        for step_cost in self._current_query.step_costs:
            step_type = "Tool Call" if step_cost.is_tool_call else "Completion"
            print(f"\nStep {step_cost.step_number} ({step_type}):")
            print(f"  Input Tokens:  {step_cost.input_tokens:,}")
            print(f"  Output Tokens: {step_cost.output_tokens:,}")
            print(f"  Cost:          ${step_cost.cost:.6f}")

            total_cost += step_cost.cost
            total_input_tokens += step_cost.input_tokens
            total_output_tokens += step_cost.output_tokens
        print("TOTAL:")
        print(f"  Total Input Tokens:  {total_input_tokens:,}")
        print(f"  Total Output Tokens: {total_output_tokens:,}")
        print(f"  Total Cost:          ${total_cost:.6f}")

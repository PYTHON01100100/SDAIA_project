import asyncio
import json
import os
import time

import structlog
from litellm import acompletion, completion_cost
from pydantic import ValidationError

from src.observability.cost_tracker import CostTracker
from src.observability.loop_detector import AdvancedLoopDetector
from src.observability.tracer import AgentStep, AgentTracer, ToolCallRecord
from src.tools.registry import registry

logger = structlog.get_logger()

class ObservableAgent:
    """
    Production-grade agent with full observability.
    
    This agent implements the ReAct pattern (Reasoning + Acting) but enhances it 
    with "Observability" - the ability to track, trace, and debug the agent's 
    internal state and actions.
    """
    def __init__(
        self,
        model: str ="gemini/gemini-3-flash-preview",
        max_steps: int = 10,
        agent_name: str = "ObservableAgent",
        verbose: bool = True,
        system_prompt: str = """
        ### Role
        You are an advanced AI Assistant powered by Gemini, designed to be autonomous, accurate, and resourceful. You operate as a "ReAct" agent (Reasoning + Acting), capable of solving complex problems by breaking them down into logical steps.

        ### Context
        You have access to a specific set of external tools (registered in your system). You are operating in a production environment where your actions, reasoning steps, and costs are strictly monitored. Users rely on you for factual, up-to-date information that goes beyond your training data.

        ### Task
        1.  **Analyze**: Deeply understand the user's intent and identify what information is missing.
        2.  **Reason**: Formulate a step-by-step plan to retrieve the necessary information.
        3.  **Act**: Execute the available tools (e.g., 'search_web', 'read_webpage') to gather evidence.
        4.  **Synthesize**: Combine the tool outputs to construct a comprehensive, well-cited, and direct answer.

        ### Constraints
        -   **Tool Usage**: You MUST use tools for any query requiring current facts or specific data. Do not rely solely on your internal knowledge.
        -   **No Hallucination**: Never invent URLs, facts, or data. If a tool returns no results, state that clearly or try a different search strategy.
        -   **Avoid Loops**: If a tool call fails or returns the same result, DO NOT repeat the exact same call. Change your search query or approach immediately to avoid triggering the Loop Detector.
        -   **Citation**: Always provide the source URL for every piece of factual information you present.
        -   **Formatting**: Present your final answer in clear Markdown (using bolding, lists, and headers).
        """,
        tools: list = None,
        
    ):
        self.model = model or os.getenv("gemini/gemini-3-flash-preview")
        self.max_steps = max_steps
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.tools = tools if tools is not None else registry.get_all_tools()
        self.verbose = verbose
        
        # TODO: Initialize observability components
        # Observability includes:
        # 1. Tracing: Recording every step (reasoning, tool calls, results).
        # 2. Loop Detection: Preventing the agent from repeating the same actions.
        # 3. Cost Tracking: Monitoring token usage and cost.
        
        self.tracer = AgentTracer(verbose=verbose)
        self.loop_detector = AdvancedLoopDetector()
        self.cost_tracker = CostTracker()
        
        
        self.active_trace_id = None
    

    async def run(self, user_query: str) -> dict:
        """Execute the agent loop with full observability."""
        # TODO: Implement the agent loop
        # 1. Start trace and cost tracking
        # 2. Loop until max_steps
        # 3. Call LLM (using acompletion)
        # 4. Log completion and cost
        # 5. Handle tool calls (execute in parallel?)
        # 6. Check for loops
        # 7. Return final answer
        # 8. Handle errors and end trace
        
        self.cost_tracker.start_query(user_query)
         
        self.active_trace_id = self.tracer.start_trace(
            agent_name=self.agent_name, 
            query=user_query, 
            model=self.model
        )
        self.loop_detector.reset()
        
        messages = [
            {"role": "system", "content": self.system_prompt or "You are a helpful assistant."},
            {"role": "user", "content": user_query}
        ]
        
        step_count = 0
        final_answer = None
        
        current_run_cost = 0.0

        try:
            while step_count < self.max_steps:
                step_count += 1
                start_time = time.time()
                
                tool_schemas = [t.to_openai_schema() for t in self.tools]

                response = await acompletion(
                    model=self.model,
                    messages=messages,
                    tools=tool_schemas,
                    tool_choice="auto"
                )

                try:
                    cost = completion_cost(completion_response=response)
                except Exception:
                    cost = 0.0
                self.cost_tracker.add_cost(cost)
                
                # self.cost_tracker.log_completion(
                #     step_number=step_count, 
                #     response=response, 
                #     is_tool_call=False
                # )
                
                response_message = response.choices[0].message
                messages.append(response_message)
                
                usage = response.get("usage", {})

                current_step = AgentStep(
                    # step_number=step_count,
                    # reasoning=response_message.content or "Processing tool calls...",
                    # model_response=response_message.to_dict()
                    
                    step_number=step_count,
                    reasoning=response_message.content or "Executing tool calls...",
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    cost_usd=cost,
                    duration_ms=(time.time() - start_time) * 1000
                )

                if response_message.tool_calls:
                    for tool_call in response_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args_str = tool_call.function.arguments
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        loop_result = self.loop_detector.check_tool_call(
                            tool_name=tool_name, 
                            tool_input=tool_args_str
                        )
                        
                        if loop_result.is_looping:
                            logger.warning(f"Loop detected: {loop_result.message}")
                            final_answer = f"Terminated due to loop: {loop_result.message}"
                            break 
                        
                        tool_start = time.time()
                         
                        try:
                            result = registry.execute_tool(tool_name, **tool_args)
                        except Exception as e:
                            result = f"Error: {str(e)}"
                            
                        tool_duration = (time.time() - tool_start) * 1000    

                        current_step.tool_calls.append(
                            ToolCallRecord(
                                # tool_name=tool_name,
                                # args=tool_args,
                                # result=result
                                
                                tool_name=tool_name,
                                tool_input=tool_args,
                                tool_output=str(result),
                                duration_ms=tool_duration
                            )
                        )

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": str(result)
                        })

                    if self.loop_detector.is_looping(messages):
                        final_answer = "Loop detected: The agent is repeating actions. Terminating."
                        break
                else:
                    final_answer = response_message.content
                    break
                
                # self.tracer.add_step(current_step)
                self.tracer.log_step(self.active_trace_id, current_step)

            if not final_answer:
                final_answer = "Exceeded maximum steps without reaching a conclusion."

        except Exception as e:
            logger.error("agent_error", error=str(e))
            final_answer = f"An error occurred: {str(e)}"
            self.tracer.end_trace(
                trace_id=self.active_trace_id, 
                output=final_answer, 
                status="error", 
                error=str(e)
            )
        else:
            self.tracer.end_trace(
                trace_id=self.active_trace_id, 
                output=final_answer, 
                status="completed"
            )
        finally:
            if self.cost_tracker._current_query:
                current_run_cost = self.cost_tracker._current_query.total_cost_usd
                
            if self.active_trace_id:
                self.tracer.end_trace(
                    trace_id=self.active_trace_id, 
                    output=str(final_answer),
                    status="completed" if step_count < self.max_steps else "max_steps_reached"
                )
            
            self.cost_tracker.end_query()

        return {
            "answer": final_answer,
            "trace_id": self.active_trace_id,
            "total_cost": self.cost_tracker.get_total_cost(),
            "steps": step_count
        }
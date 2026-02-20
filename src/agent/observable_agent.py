import asyncio
import json
import os
import time
from typing import List, Dict, Any

import structlog
from openai import AsyncOpenAI

logger = structlog.get_logger()


# ==============================
# OpenRouter Client
# ==============================
client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "AI Agents Project",
    },
)


class ObservableAgent:
    """
    Production-ready Observable Agent
    Supports:
    - ReAct loop
    - Tool calling
    - Token tracking
    - Cost estimation
    - Loop detection
    """

    def __init__(
        self,
        model: str = None,
        max_steps: int = 5,
        agent_name: str = "ObservableAgent",
        verbose: bool = True,
        system_prompt: str = None,
        tools: list = None,
    ):
        self.model = model or os.getenv("MODEL_NAME", "z-ai/glm-4.5-air:free")
        self.max_steps = max_steps
        self.agent_name = agent_name
        self.system_prompt = system_prompt or f"You are {agent_name}."
        self.tools = tools or []
        self.verbose = verbose

        # Observability
        self.trace_log: List[Dict[str, Any]] = []
        self.loop_detector = set()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    # ======================================
    # Convert Tools → OpenAI Schema
    # ======================================
    def _convert_tools_to_openai_schema(self):
        return [tool.to_openai_schema() for tool in self.tools]

    # ======================================
    # Cost Estimation (Approximate) - note : note api call for cost tracking, just estimation based on token counts
    # ======================================
    def _estimate_cost(self) -> float:
        input_cost_per_1k = 0.0003
        output_cost_per_1k = 0.0006

        input_cost = (self.total_input_tokens / 1000) * input_cost_per_1k
        output_cost = (self.total_output_tokens / 1000) * output_cost_per_1k

        return round(input_cost + output_cost, 6)

    # ======================================
    # Main Agent Loop
    # ======================================
    async def run(self, user_query: str) -> dict:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query},
        ]

        openai_tools = self._convert_tools_to_openai_schema()
        final_answer = None

        for step in range(1, self.max_steps + 1):
            start_time = time.time()

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                tool_choice="auto" if openai_tools else None,
            )

            message = response.choices[0].message

            # ======================
            # Token Tracking
            # ======================
            if response.usage:
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens

            step_record = {
                "step": step,
                "model_response": message.content,
                "tools_called": [],
                "latency_sec": round(time.time() - start_time, 3),
            }

            if self.verbose:
                print(f"\n[{self.agent_name} - Step {step}]")
                print("Response:", message.content)

            # ======================
            # Loop Detection
            # ======================
            if message.content and message.content in self.loop_detector:
                if self.verbose:
                    print("⚠️ Loop detected. Stopping execution.")
                break

            if message.content:
                self.loop_detector.add(message.content)

            # ======================
            # Tool Calling
            # ======================
            if message.tool_calls:
                messages.append(message)

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    tool = next((t for t in self.tools if t.name == tool_name), None)

                    if not tool:
                        continue

                    try:
                        result = tool.execute(**arguments)
                    except Exception as e:
                        result = f"Tool execution failed: {str(e)}"

                    step_record["tools_called"].append(
                        {tool_name: result}
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result),
                        }
                    )

                    if self.verbose:
                        print(f"🔧 Tool executed: {tool_name}")

                self.trace_log.append(step_record)
                continue

            # ======================
            # Final Answer
            # ======================
            final_answer = message.content
            messages.append(message)
            self.trace_log.append(step_record)
            break

        return {
            "agent_name": self.agent_name,
            "model_used": self.model,
            "answer": final_answer,
            "trace_log": self.trace_log,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost_usd": self._estimate_cost(),
        }


# ======================================
# Standalone Test
# ======================================
if __name__ == "__main__":

    async def test():
        agent = ObservableAgent(max_steps=3)
        result = await agent.run("Explain what multi-agent systems are.")
        print(json.dumps(result, indent=2))

    asyncio.run(test())

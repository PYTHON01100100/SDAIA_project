import inspect
from typing import Any, Callable, Dict, Optional, List
from pydantic import BaseModel, create_model, ValidationError

# ===========================
# Tool Wrapper
# ===========================
class Tool:
    def __init__(self, name: str, func: Callable, description: str):
        self.name = name
        self.func = func
        self.description = description
        self.model = self._create_pydantic_model(func)

    def _create_pydantic_model(self, func: Callable) -> type(BaseModel):
        sig = inspect.signature(func)
        fields = {}

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            annotation = (
                param.annotation
                if param.annotation != inspect.Parameter.empty
                else str
            )

            default = (
                param.default
                if param.default != inspect.Parameter.empty
                else ...
            )

            fields[param_name] = (annotation, default)

        return create_model(f"{self.name}Schema", **fields)

    def to_openai_schema(self) -> dict:
        schema = self.model.model_json_schema()

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                    "additionalProperties": False,
                },
            },
        }

    def execute(self, **kwargs) -> Any:
        try:
            validated_args = self.model(**kwargs)
            result = self.func(**validated_args.model_dump())

            # 🔥 أهم تعديل: نحول أي نتيجة لنص
            if result is None:
                return "No result returned."

            if isinstance(result, (dict, list)):
                return str(result)  # مهم عشان LLM ما يطيح

            return result

        except ValidationError as e:
            return f"Validation error in tool '{self.name}': {str(e)}"
        except Exception as e:
            return f"Execution error in tool '{self.name}': {str(e)}"


# ===========================
# Registry
# ===========================
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, name: str, description: str, category: str = "general"):
        def decorator(func: Callable):
            tool = Tool(name=name, func=func, description=description)

            self._tools[name] = tool
            self._categories.setdefault(category, []).append(name)

            return func

        return decorator

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get_tools_by_category(self, category: str) -> List[Tool]:
        return [
            self._tools[name]
            for name in self._categories.get(category, [])
        ]

    def execute_tool(self, name: str, **kwargs) -> Any:
        tool = self.get_tool(name)

        if not tool:
            return f"Tool '{name}' not found."

        return tool.execute(**kwargs)


# ===========================
# Global Registry Instance
# ===========================
registry = ToolRegistry()

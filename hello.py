from functools import lru_cache
import subprocess
from typing import Any
import anthropic
import os
import dotenv
from dataclasses import dataclass


@dataclass
class Property:
    description: str
    type: str
    required: bool

    def to_dict(self):
        return {
            "description": self.description,
            "type": self.type,
        }


@dataclass
class Tool:
    name: str
    description: str
    function: callable
    properties: dict[str, Property]

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {k: v.to_dict() for k, v in self.properties.items()},
                "required": [k for k, v in self.properties.items() if v.required],
            },
        }

    def call(self, input: dict):
        return self.function(**input)


class ModelMessageHandler:
    def __init__(self):
        pass

    def handle_message(self, message: str):
        print(f"AGENT: {message}")


class ModelSession:
    def __init__(
        self,
        handler: ModelMessageHandler,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024,
    ):
        self.handler = handler
        self.model = model
        self.max_tokens = max_tokens
        self.messages = []
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.tools = {}
        self._tools_cache = []

    def send_message(self, message: str) -> None:
        self.messages.append({"role": "user", "content": message})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=self.messages,
            tools=self._tools_cache,
        )
        self.handle_response(response)

    def handle_response(self, response: Any) -> None:
        self.messages.append({"role": "assistant", "content": response.content})
        tool_use_results = []
        for content in response.content:
            if content.type == "text":
                self.handler.handle_message(content.text)
            elif content.type == "tool_use":
                tool_use_results.append(self.handle_tool_use(content))
            else:
                raise ValueError(f"Unknown content type: {content.type}")
        if tool_use_results:
            self.send_message(tool_use_results)

    def handle_tool_use(self, tool_use_block: Any) -> dict[str, str]:
        tool_name = tool_use_block.name
        tool = self.tools[tool_name]
        result = tool.call(tool_use_block.input)
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_block.id,
            "content": str(result),
        }

    def add_tool(self, tool: Tool):
        if tool.name in self.tools:
            raise ValueError(f"Tool {tool.name} already exists")
        self.tools[tool.name] = tool
        self._tools_cache.append(tool.to_dict())
        print(self._tools_cache)


def execute_shell_code(code: str):
    return subprocess.run(code, shell=True, capture_output=True, text=True).stdout


def main():
    dotenv.load_dotenv()
    print("Hello from debug-agent!")
    model = ModelSession(handler=ModelMessageHandler())
    shell_tool = Tool(
        name="shell",
        description="Execute shell code on the host machine",
        function=execute_shell_code,
        properties={
            "code": Property(
                description="The shell code to execute", type="string", required=True
            )
        },
    )
    model.add_tool(shell_tool)
    resp = model.send_message("Hello, Claude, I am steve.")
    resp = model.send_message("What's my name?")
    resp = model.send_message("Is Python installed?")


if __name__ == "__main__":
    main()

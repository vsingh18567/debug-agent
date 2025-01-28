from functools import lru_cache
from typing import Any
import anthropic
import os
import dotenv

from tools import Tool, TOOLS


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
            system="You are an assistant to help software developers debug their code. Your focus is on correctness and performance. Correctness is more important than performance. Ask clarifying questions.",
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


def main():
    dotenv.load_dotenv()
    model = ModelSession(handler=ModelMessageHandler())
    for t in TOOLS:
        model.add_tool(t)
    resp = model.send_message(
        "I have a bug in my quicksort implementation in qsort.py. Fix it."
    )


if __name__ == "__main__":
    main()

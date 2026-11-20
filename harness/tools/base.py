from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Tool:
    """One capability the agent has: its name, how it is described to the model,
    and the Python function that actually runs."""

    name: str
    description: str
    parameters: dict  # JSON schema for the arguments
    func: Callable[..., str]

    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
from typing import Any

from pydantic import BaseModel


class Command(BaseModel):
    command: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Command":
        clz = COMMAND_NAME_TO_CLASS[data["command"]]
        return clz(**data)

class StartFlowCommand(Command):
    flow: str

class SetSlotsCommand(Command):
    slots: dict[str, Any]

class CancelFlowCommand(Command):
    pass


class ResumeFlowCommand(Command):
    flow: str | None = None



COMMAND_NAME_TO_CLASS = {
    "start_flow": StartFlowCommand,
    "set_slots": SetSlotsCommand,
    "cancel_flow": CancelFlowCommand,
    "resume_flow": ResumeFlowCommand,
}
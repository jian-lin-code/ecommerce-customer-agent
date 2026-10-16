import asyncio
from typing import Any

from domain.state import DialogueState
from task.action.base import Action, ActionResult


class ActionListen(Action):
    """
    什么都不做，返回空的ActionResult
    """
    name = "action_listen"

    async def run(self, state: DialogueState, action_kwargs: dict[str, Any]) -> ActionResult:
        print("action_listen")
        return ActionResult()


if __name__ == '__main__':
    action =  ActionListen()
    asyncio.run(action.run(None, None))
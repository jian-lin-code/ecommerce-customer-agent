from typing import Any

from pydantic import BaseModel

from task.action.registry import ActionRegistry
from task.action.base import ActionResult
from domain.state import DialogueState


class ActionCall(BaseModel):
    action_name: str
    action_kwargs: dict[str, Any] = {}

# 面向修改关闭，面向扩展开放
class ActionRunner:
    """
    通过给定的action_call，执行action
    """
    def __init__(self, registry: ActionRegistry) -> None:
        self.registry = registry

    async def run(self, action_call: ActionCall, state: DialogueState) -> ActionResult:
        # 1. 获取action的名字
        action_name = action_call.action_name

        # 2. 从Action注册中心获取名字对应的Action的实例对象
        action = self.registry.get(action_name)

        # 3. 调用具体Action的逻辑
        return await action.run(state, action_call.action_kwargs)
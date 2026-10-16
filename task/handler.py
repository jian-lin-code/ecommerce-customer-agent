from domain.messages import BotMessage
from domain.state import DialogueState
from task.action.runner import ActionRunner
from task.command.models import Command
from task.command.processor import CommandProcessor
from task.flow.executor import FlowExecutor
from task.flow.flows import FlowsList


class TaskHandler:

    def __init__(
            self,
            flows:FlowsList,
            command_processor: CommandProcessor,
            flow_executor: FlowExecutor,
            action_runner: ActionRunner
    ):
        self.flows = flows
        self.command_processor = command_processor
        self.flow_executor = flow_executor
        self.action_runner = action_runner

    async def handle(self, commands: list[Command], state: DialogueState) -> list[BotMessage]:

        # 阶段1:把命令应用到 state（修改state状态）
        self.command_processor.run(commands, state, self.flows)

        # 阶段2:推进流程,生成回复(后面两节 TODO)
        messages: list[BotMessage] = await self.flow_executor.run_task(state, self.flows, self.action_runner)

        return messages
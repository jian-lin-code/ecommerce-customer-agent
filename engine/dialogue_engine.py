import json
import time

from jinja2.utils import object_type_repr
from loguru import logger

from clarify.responder import ClarifyResponder
from domain.state import DialogueState
from domain.messages import UserMessage, ProcessResult, BotMessage, MessageType
from knowledge.intents import KNOWLEDGE_INTENTS
from plan.models import TurnPlan, TurnPlanValidationResult, ClarifyReason
from plan.turn_planner import TurnPlanner
from plan.turn_validator import TurnPlanValidator
from task.command.models import Command, SetSlotsCommand
from task.flow.flows import FlowsList
from task.flow.steps import CollectFlowStep
from task.handler import TaskHandler
from knowledge.handler import KnowLedgeHandler
from chitchat.handler import ChitChatHandler

class DialogueEngine:
    def __init__(
            self,
            turn_planner: TurnPlanner,
            task_handler: TaskHandler,
            knowledge_handler: KnowLedgeHandler,
            chitchat_handler: ChitChatHandler,
            clarify_responder: ClarifyResponder,
            turn_plan_validator: TurnPlanValidator
    ) -> None:
        self.turn_planner = turn_planner
        self.task_handler = task_handler
        self.knowledge_handler = knowledge_handler
        self.chitchat_handler = chitchat_handler
        self.clarify_responder = clarify_responder
        self.turn_plan_validator = turn_plan_validator

    async def process_message(self, dialogue_state: DialogueState,
                            user_message: UserMessage) -> ProcessResult:
        # 1. 准备会话
        self._prepare_session(dialogue_state)

        # 2. 开启本轮turn
        dialogue_state.begin_turn(user_message)

        # 3. 按消息类型分流
        if user_message.type is MessageType.TEXT:
            # 3.1 文本消息
            messages = await self._handle_text_message(dialogue_state)
        else:
            # 3.2 对象消息
            assert user_message.object is not None, "user_message.object不能为空"
            dialogue_state.set_focused_object(user_message.object)
            messages = await self._handle_object_message(dialogue_state)

        # 4. 把本轮回复写入turn
        dialogue_state.pending_turn.bot_messages.extend(messages)
        # 提交:turn 进入 session 历史
        dialogue_state.commit_pending_turn()

        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=messages

        )

    def _prepare_session(self, dialogue_state: DialogueState) -> None:
        """
        准备会话
        :param dialogue_state:
        :return:
        """

        # 1. 获取当前会话
        session = dialogue_state.current_session()

        # 2. 如果当前会话不存在，则创建一个会话
        if session is None:
            dialogue_state.start_session()
            return

        # 3. 判断会话是否超时
        now = time.time()
        if now - session.last_activity_at > 60 * 60:  # 1小时
            # 关闭会话
            dialogue_state.close_current_session()
            # 重置运行时状态
            dialogue_state.reset_runtime_state_for_new_session()
            # 创建会话
            dialogue_state.start_session()
        else:
            # 更新会话（会话续期）
            session.last_activity_at = now

    # 文本消息处理
    async def _handle_text_message(self, dialogue_state: DialogueState) -> list[BotMessage]:

        # 1. 调 LLM 生成本轮计划（确定任务轨道）
        turn_plan: TurnPlan = await self.turn_planner.predict(dialogue_state, self.task_handler.flows,self.knowledge_handler.knowledge_intents)
        logger.info(f'turn_plan:{turn_plan}')
        # 2. 防幻觉校验(本节不实现,后面讲) TurnPlanValidator用于校验
        validate_result:TurnPlanValidationResult = self.turn_plan_validator.validate(
            turn_plan=turn_plan,
            flow_list=self.task_handler.flows,
            state=dialogue_state,
            intents=self.knowledge_handler.knowledge_intents)

        if not validate_result.valid:
            reason = validate_result.reason
            assert reason is not None, "校验失败时reason不能为空"
            return await self.clarify_responder.respond(dialogue_state, reason)

        # 3.1 办理业务
        if turn_plan.task is not None:
            return await self.task_handler.handle(
                commands=turn_plan.task.commands,
                state=dialogue_state,
            )
        elif turn_plan.knowledge is not None:
            # 3.2 咨询业务
            return await self.knowledge_handler.handle(turn_plan.knowledge.intents,dialogue_state)
        else:
            # 3.3 闲聊
            return await self.chitchat_handler.handle(state=dialogue_state)

    # 对象消息处理 order / product
    async def _handle_object_message(self,dialogue_state:DialogueState) ->list[BotMessage]:
        """
        处理对象消息
        :param user_message:
        :param dialogue_state:
        :return:
        """
         # 1.将对象解析成command(SetSlotsCommand)
        commands = self._resolve_object_commands(
            dialogue_state=dialogue_state,
            flows=self.task_handler.flows
        )

        # 2. 判断command是否存在(流程的步骤刚好需要你点击的卡片)
        if commands:
            # 场景 A:对象能填当前槽 → 转成命令,推进流程
            return await self.task_handler.handle(commands=commands, state=dialogue_state)

        # 有流程，没有匹配到 slot
        # 如果用户正在一个流程中,不打断,让流程继续。
        # 场景 C:在流程里但槽不匹配 → 不打断,空命令让流程继续
        if dialogue_state.active_task is not None:
            return await self.task_handler.handle(commands=[], state=dialogue_state)

        # 没有流程：
        # 场景 B:没有流程 → 澄清
        return await self.clarify_responder.respond(
            state=dialogue_state,
            reason=ClarifyReason.OBJECT_REQUIRES_INTENT,
        )

    def _resolve_object_commands(self, dialogue_state:DialogueState, flows:FlowsList)->list[Command]:
        """
        将消息转成command
        :param user_message:
        :param dialogue_state:
        :param flows:
        :return:
        """

        # 1.获取聚焦对象
        focused_object = dialogue_state.focused_object
        if focused_object is None:
            return []

        # 2.获取聚焦对象的类型
        object_type = focused_object.type

        # 3.1. 判读对象的类型 order
        if object_type == "order":
            if self._flow_has_unfilled_collect_slot(dialogue_state,flows,"order_number"):
                return [SetSlotsCommand(command="set_slots", slots={"order_number": focused_object.id})]
            return []

        # 3.2. 判读对象的类型 product
        if object_type == "product":
            if self._flow_has_unfilled_collect_slot(dialogue_state, flows, "product_id"):
                return [SetSlotsCommand(command="set_slots", slots={"product_id": focused_object.id})]

            return []

        return []

    def _flow_has_unfilled_collect_slot(self, dialogue_state:DialogueState, flows:FlowsList, slot_name):
        """
            判断流程中是否有未填的收集槽位
            :param state:
            :param flows:
            :param slot_name:
            :return:
            """

        # 1. 获取活跃任务
        active_task = dialogue_state.active_task

        # 2. 是否存在活跃任务
        if active_task is None:
            # 不存在
            return False

        # 3. 根据活跃任务的id获取流程
        flow_id = active_task.flow_id
        flow = flows.get_flow_by_id(flow_id)
        if flow is None:
            # 不存在
            return False

        # 4. 判断该流程中的当前槽位是否已经填过
        if active_task.slots.get(slot_name):
            return False

        # 5. 遍历流程的步骤,查找是否存在收集这个槽位的步骤
        for step in flow.steps:
            if isinstance(step, CollectFlowStep) and step.slot_name == slot_name:
                return True

        return False

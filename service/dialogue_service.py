from api.schemas import HistoryMessage
from domain.messages import UserMessage, ProcessResult
from domain.state import DialogueState
from prompts.history_builder import HistoryBuilder
from repository.dialogue_state_repository import DialogueStateRepository
from engine.dialogue_engine import DialogueEngine


class DialogueService:
    """
    处理对话的业务类
    """

    def __init__(
            self,
            dialogue_state_repository: DialogueStateRepository,
            dialogue_engine: DialogueEngine):
            self.dialogue_state_repository = dialogue_state_repository
            self.dialogue_engine = dialogue_engine

    async def process_message(self, user_message: UserMessage) -> ProcessResult:
        """
        核心处理逻辑(IO：很慢/计算:调用LLM以及执行引擎、比较慢)
        :param user_message:
        :return:
        """
        # 1. 通过 repository 根据 sender_id 加载对话状态(O 阶段)
        dialogue_state: DialogueState = await self.dialogue_state_repository.load_state(user_message.sender_id)
        # 2. 使用 engine 根据对话状态处理最新消息
        process_result: ProcessResult = await self.dialogue_engine.process_message(dialogue_state, user_message)
        # 3. 通过 repository 保存最新的对话状态(I 阶段)
        await self.dialogue_state_repository.save_state(dialogue_state)
        # 4. 返回本轮处理结果
        return process_result

    async def load_chat_history(self, sender_id: str) -> list[HistoryMessage]:

        # 根据 sender_id 从数据库加载完整 DialogueState
        state = await self.dialogue_state_repository.load_state(sender_id)

        # 遍历 state.sessions，把每个 turn 展开成消息列表
        chat_messages: list[HistoryMessage] = []
        for session in state.sessions:
            for turn in session.turns:
                chat_messages.append(HistoryBuilder.get_user_message(session.session_id, turn.user_message))
                chat_messages.extend([
                    HistoryBuilder.get_bot_message(session.session_id, b_msg) for b_msg in turn.bot_messages
                ])

        # 返回给 router 组装的结果
        return chat_messages
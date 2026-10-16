from pathlib import Path

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chitchat.handler import ChitChatHandler
from chitchat.responder import ChitChatResponder
from clarify.responder import ClarifyResponder
from knowledge.handler import KnowLedgeHandler
from knowledge.intents import KNOWLEDGE_INTENTS
from knowledge.providers import ProductAPIProvider, OrderAPIProvider, FAQProvider, RAGProvider
from knowledge.registry import KnowledgeProviderRegistry
from knowledge.responder import KnowledgeResponder
from plan.turn_planner import TurnPlanner
from plan.turn_validator import TurnPlanValidator
from service.dialogue_service import DialogueService
from repository.dialogue_state_repository import DialogueStateRepository
from engine.dialogue_engine import DialogueEngine

# 注意：必须通过这种方式引入database，需要的时候再获取： database.async_session()
from infrastructure import database
from task.command.processor import CommandProcessor
from task.flow.executor import FlowExecutor
from task.flow.loader import FlowLoader
from task.handler import TaskHandler
from task.action.builder import build_action_runner

# 不要通过这种方式引入async_session，会是一个NoneType
# from atguigu.infrastructure.database import async_session

async def get_session():
    """
    实际流程：
        进入 async with → 打开 session
        yield session → 把 session 交给repository函数使用
        路由函数执行完毕 → 回到 yield 之后
        退出 async with → 自动关闭 session ✅
    :return:
    """
    async with database.async_session() as session:  # 异步方式获取session  获取session要网络传输（耗时的）
        yield session


async def get_dialogue_state_repository(session: AsyncSession = Depends(get_session)):
    """
    创建 DialogueStateRepository 实例

    依赖链执行顺序：
       1. get_session() 打开 session 并 yield
       2. 这里拿到 session，创建 Repository
       3. Repository 被Service使用，Service被路由函数使用
       4. 路由函数返回后，get_session() 继续执行，自动关闭 session
    :param session:
    :return:
    """
    return DialogueStateRepository(session=session)
    # 3. 函数返回后，FastAPI 继续执行 get_session() y


async def get_engine():
    base_path = Path(__file__).parent.parent
    user_flow_path = base_path / 'flow_config' / 'user_flows.yml'
    system_flow_path = base_path / 'flow_config' / 'system_flows.yml'
    flows = FlowLoader().load_many([user_flow_path, system_flow_path])
    return DialogueEngine(
        turn_planner=TurnPlanner(),
        task_handler=TaskHandler(flows=flows,command_processor=CommandProcessor(),action_runner=build_action_runner(),flow_executor=FlowExecutor()),
        knowledge_handler=KnowLedgeHandler(
            knowledge_intents=KNOWLEDGE_INTENTS,
            provider_registry=KnowledgeProviderRegistry([ProductAPIProvider(),OrderAPIProvider(),FAQProvider(),RAGProvider()]),
            knowledge_responder=KnowledgeResponder()
        ),
        turn_plan_validator=TurnPlanValidator(),
        clarify_responder=ClarifyResponder(),
        chitchat_handler=ChitChatHandler(responder=ChitChatResponder())
    )

async def get_dialogue_service(
        dialogue_state_repository: DialogueStateRepository = Depends(get_dialogue_state_repository),
        dialogue_engine: DialogueEngine = Depends(get_engine)
) -> DialogueService:
    return DialogueService(dialogue_state_repository=dialogue_state_repository, dialogue_engine=dialogue_engine)
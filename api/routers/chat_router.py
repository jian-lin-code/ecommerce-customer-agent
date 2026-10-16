import uuid
from fastapi import APIRouter, Depends,Request

from api.dependencies import get_dialogue_service
from api.schemas import ChatRequest, ChatResponse, ChatBotMessage, ChatObject, HistoryResponse, HistoryMessage
from domain.messages import ProcessResult, UserMessage, MessageType, FocusedObject
from service.dialogue_service import DialogueService

router = APIRouter()


# 定义路由接口

@router.post("/api/chat")
async def chat_endpoint(
        chat_request: ChatRequest,
        dialogue_service: DialogueService = Depends(get_dialogue_service)
) -> ChatResponse:
    # 1. 处理输入接口模型
    user_message = _build_user_message(chat_request)
    # 2. 业务处理
    process_result: ProcessResult = await dialogue_service.process_message(user_message)
    # 3. 处理输出接口模型
    return _build_chat_response(process_result)

def _build_user_message(chat_request: ChatRequest) -> UserMessage:
    """
    将请求数据模型转换为领域数据模型 供业务使用
    :param chat_request:
    :return:
    """
    return UserMessage(
        sender_id=chat_request.sender_id,
        message_id=chat_request.message_id if chat_request.message_id else str(uuid.uuid4()),
        type=MessageType.TEXT if chat_request.text else MessageType.OBJECT,
        text=chat_request.text,
        # 解构时不能是一个对象，必须转成字典
        object=FocusedObject(**chat_request.object.model_dump(mode='json')) if chat_request.object else None
    )


def _build_chat_response(process_result: ProcessResult) -> ChatResponse:
    return ChatResponse(
        sender_id=process_result.sender_id,
        message_id=process_result.message_id,
        messages=[
            ChatBotMessage(
                text=bot_msg.text,
                object=ChatObject(**bot_msg.object.model_dump(mode='json')) if bot_msg.object else None
            )
            for bot_msg in process_result.messages
        ]
    )

@router.get('/api/chat/history')
async def history(sender_id: str, dialogue_service: DialogueService = Depends(get_dialogue_service)) -> HistoryResponse:
    chat_message_response: list[HistoryMessage] = await dialogue_service.load_chat_history(sender_id)
    return HistoryResponse(sender_id=sender_id, messages=chat_message_response)
from enum import Enum

from pydantic import BaseModel, Field


class FocusedObject(BaseModel):
    """
    聚焦对象
    """
    id: str  # 对象的唯一标识（如order_id、product_id）
    type: str  # 对象类型（如 "order", "product"）
    title: str  # 对象的标题（如 “纯棉T恤”）
    attributes: dict = Field(default_factory=dict) # 其他额外信息


class MessageType(Enum):
    """
    消息类型
    """
    TEXT = "text"  # 文本类型
    OBJECT = "object"  # 对象类型

class UserMessage(BaseModel):
    sender_id: str  # 用户ID(必填字段)
    message_id: str  # 消息ID(必填字段)
    type: MessageType  # 消息类型（text 或 object）必填字段
    text: str | None = None  # 文本消息(用户说的话)
    object: FocusedObject | None = None  # 对象类型的消息(用户点击的对象)

class BotMessage(BaseModel):
    text: str | None = None # 机器人回复的话
    object: FocusedObject | None = None # 机器人返回的对象

class ProcessResult(BaseModel):
    sender_id: str  # 用户ID
    message_id: str  # 消息ID(内部生成)
    messages: list[BotMessage]  # 回复消息（机器人回复的所有消息都给前端）

if __name__ == '__main__':
    pass
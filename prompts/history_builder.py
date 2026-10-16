import json
from typing import Dict, Any

from api.schemas import ChatObject, HistoryMessage
from domain.state import Turn
from domain.messages import UserMessage, BotMessage, FocusedObject, MessageType


class HistoryBuilder:
    """
    1. 将用户消息的UserMessage对象序列化为字符串
    "USER: 我准备查询订单信息"
    2. 将历史对话的Q(UserMessage)A(BotMessage)对象序列化为字符串：
    "USER: 我想查询物流信息\n BOT: 好的，先提供订单编号"
    """

    @staticmethod
    def build(turns: list[Turn]) -> str:
        """
        将多轮对话列表转换成字符串形式
        :param turns:
        :return:
        """

        msgs: list[str] = []
        for turn in turns:
            # 1. 处理用户消息
            user_message = turn.user_message
            user_message_str = HistoryBuilder._render_user_message(user_message)
            msgs.append(f"USER:{user_message_str}")
            # 2. 处理机器人消息
            for bot_msg in turn.bot_messages:
                bot_msg_str = HistoryBuilder._render_bot_message(bot_msg)
                msgs.append(f"BOT:{bot_msg_str}")

        return "\n".join(msgs)

    @staticmethod
    def _render_user_message(user_message: UserMessage):

        if user_message.type is MessageType.TEXT:
            return HistoryBuilder._render_text_msg(user_message.text)
        else:
            return HistoryBuilder._render_obj_msg(user_message.object)
    @staticmethod
    def render_user_message(user_message: UserMessage):
        return HistoryBuilder._render_user_message(user_message)

    @staticmethod
    def _render_bot_message(bot_msg: BotMessage):

        if bot_msg.text:
            return HistoryBuilder._render_text_msg(bot_msg.text)
        else:
            return HistoryBuilder._render_obj_msg(bot_msg.object)

    @staticmethod
    def _render_text_msg(text):
        return text.strip()

    @staticmethod
    def _render_obj_msg(object_msg: FocusedObject):

        label = "订单对象" if object_msg.type == "order" else "商品对象"
        id = object_msg.id
        title = object_msg.title
        attributes: Dict[str, Any] = object_msg.attributes
        # attributes_str = ",".join([f"{key}:{value}" for key, value in attributes.items()])
        # 字典转字符串
        attributes_str = json.dumps(attributes, ensure_ascii=False)
        return f"[label={label}, id={id}, title={title}, attributes={attributes_str}]"

    def get_user_message(session_id: str, user_message: UserMessage) -> HistoryMessage:
        user_obj = ChatObject(**user_message.object.model_dump()) if user_message.object else None
        return HistoryMessage(
            session_id=session_id,
            role="user",
            text=user_message.text,
            object=user_obj,
        )

    @staticmethod
    def get_bot_message(session_id: str, bot_messages: BotMessage) -> HistoryMessage:
        bot_obj = ChatObject(**bot_messages.object.model_dump()) if bot_messages.object else None
        return HistoryMessage(
            session_id=session_id,
            role="bot",
            text=bot_messages.text,
            object=bot_obj,
        )
if __name__ == '__main__':

    """
    测试 HistoryBuilder 的 build 方法
    """

    def test_build_single_text_turn():
        """测试单轮纯文本对话"""
        # 创建用户消息
        user_msg = UserMessage(
            sender_id="user_001",
            message_id="msg_001",
            type=MessageType.TEXT,
            text="我想查询订单状态"
        )

        # 创建机器人回复
        bot_msg1 = BotMessage(text="好的，我们先处理订单状态查询")
        bot_msg2 = BotMessage(text="请告诉我你的订单号。")

        # 创建轮次
        turn = Turn(
            turn_id="turn_001",
            user_message=user_msg,
            bot_messages=[bot_msg1, bot_msg2]
        )

        # 构建历史对话
        result = HistoryBuilder.build([turn])
        print(f"结果:\n{result}")


    def test_build_with_object_message():

        """测试包含对象类型的消息"""

        # 用户点击了一个订单对象
        focused_obj = FocusedObject(
            id="order_12345",
            type="order",
            title="iPhone 15 Pro Max",
            attributes={"price": "9999", "status": "已发货"}
        )

        # 创建用户消息
        user_msg = UserMessage(
            sender_id="user_001",
            message_id="msg_001",
            type=MessageType.OBJECT,
            object=focused_obj
        )

        # 创建机器人回复
        bot_msg = BotMessage(text="我看到您点击了这个订单，请问需要什么帮助？")

        # 创建轮次
        turn = Turn(
            turn_id="turn_001",
            user_message=user_msg,
            bot_messages=[bot_msg]
        )

        # 构建历史对话
        result = HistoryBuilder.build([turn])
        print(f"结果:\n{result}")

    # 运行所有测试
    test_build_single_text_turn()
    print("_________")
    test_build_with_object_message()
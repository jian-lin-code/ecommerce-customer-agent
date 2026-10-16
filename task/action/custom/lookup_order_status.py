from typing import Any

from domain.state import DialogueState
from task.action.base import Action, ActionResult
from task.action.custom.shared import fetch_order


class LookupOrderStatusAction(Action):
    name = "action_lookup_order_status"

    async def run(self, state: DialogueState, action_kwargs: dict[str, Any]) -> ActionResult:

        # 调用fetch_order接口
        order_number = state.active_task.slots.get("order_number")
        data = await fetch_order(order_number)

        # 错误处理
        if data is None:
            return ActionResult(slot_updates={
                "order_status": "查询失败",
                "order_summary": "暂时无法查到该订单信息，请稍后再试。",
            })

        # 将订单数据拼成一句摘要
        amount = data.get("amount")
        items = data.get("items")

        # 处理商品标题，兼容空列表场景
        suffix = "" if len(items) == 1 else "等"
        title_part = f"商品：{items[0].get('title')}{suffix}。"

        order_summary = f"订单金额 ¥{amount}。{title_part}"

        return ActionResult(
            slot_updates={
                "order_status": data.get("status_desc") or data.get("status"),
                "order_summary": order_summary
            }
        )
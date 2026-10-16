from typing import Any

from domain.state import DialogueState
from task.action.base import Action, ActionResult
from task.action.custom.shared import fetch_logistics


class LookupLogisticsAction(Action):
    name = "action_lookup_logistics"

    async def run(self, state: DialogueState, action_kwargs: dict[str, Any]) -> ActionResult:
        order_number = state.active_task.slots.get("order_number")
        payload = await fetch_logistics(order_number)

        if payload is None:
            return ActionResult(slot_updates={
                "tracking_number": "未知",
                "logistics_company": "未知",
                "logistics_status": "暂时无法查到物流信息，请稍后再试。",
            })

        return ActionResult(slot_updates={
            "tracking_number": payload.get("tracking_number"),
            "logistics_company": payload.get("logistics_company"),
            "logistics_status": payload.get("status_desc") or payload.get("status"),
        })
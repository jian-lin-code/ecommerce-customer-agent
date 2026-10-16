from typing import Any

from jinja2 import Template
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from domain.messages import BotMessage
from domain.state import DialogueState
from infrastructure.llm import llm
from prompts.history_builder import HistoryBuilder
from task.action.base import Action, ActionResult


class ActionResponse(Action):
    name = "action_response"

    async def run(self, state: DialogueState, action_kwargs: dict[str, Any]) -> ActionResult:
        """
        响应内容
        :param state:
        :param action_kwargs:
        :return:
        """

        mode = action_kwargs.get("mode", "static")
        if mode == "static":
            text = action_kwargs['text']
            rendered_text = self._render_text(text, state)
            return ActionResult(messages=[BotMessage(text=rendered_text)])

        elif mode == "rephrase":
            text = action_kwargs['text']
            rendered_text = self._render_text(text, state)
            prompt_text = action_kwargs['prompt']
            message = await self._call_llm(prompt_text, state, rendered_text)
            return ActionResult(messages=[BotMessage(text=message)])

        else:  # generate
            prompt_text = action_kwargs['prompt']
            message = await self._call_llm(prompt_text, state)
            return ActionResult(messages=[BotMessage(text=message)])

    @staticmethod
    def _render_text(text: str, state: DialogueState) -> str:
        # 把模板里的 {{  }} 替换成真实值。
        template = Template(text)
        result = template.render(
            slots=state.active_task.slots if state.active_task else {},
            context=state.active_system_task or state.active_task,
        )
        return result

    @staticmethod
    async def _call_llm(prompt_text: str, state: DialogueState, rendered_text: str = "") -> str:
        """
        rephrase 和 generate 都走这个方法，区别在传不传 rendered_text
        :param prompt_text:
        :param state:
        :param rendered_text:
        :return:
        """
        prompt = PromptTemplate.from_template(prompt_text)
        chain = prompt | llm | StrOutputParser()

        bot_message = await chain.ainvoke({
            "history": HistoryBuilder.build(state.current_session().turns),
            "user_message": HistoryBuilder.render_user_message(state.pending_turn.user_message),
            "current_response": rendered_text,
        })
        return bot_message

if __name__ == '__main__':

    data = "好的，订单{{ order_number }}的退款申请已提交"
    template = Template(data)
    res = template.render(order_number="12345")

    # data = "好的，订单{{ slots.order_number }}的退款申请已提交"
    # template = Template(data)
    # res = template.render(slots={"order_number": "12345"})
    print(res)

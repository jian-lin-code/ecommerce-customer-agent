from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from infrastructure.llm import llm
from domain.messages import UserMessage, BotMessage
from domain.state import Turn
from prompts.history_builder import HistoryBuilder
from prompts.loader import load_prompt
from knowledge.providers import KnowledgeChunk


class KnowledgeResponder:

    async def respond(
            self,
            user_message: UserMessage,
            recent_turns: list[Turn],
            chunks: list[KnowledgeChunk]
    ) -> list[BotMessage]:
        # 准备提示词上下文
        user_message = HistoryBuilder._render_user_message(user_message)
        history = HistoryBuilder.build(recent_turns)
        knowledge_content = "\n\n".join([chunk.content for chunk in chunks])

        # 构造chain
        prompt_text = load_prompt("knowledge_respond")
        prompt = PromptTemplate.from_template(
            prompt_text,
            template_format="jinja2"
        )
        chain = prompt | llm | StrOutputParser()

        # 运行chain
        response = await chain.ainvoke({
            "user_message": user_message,
            "history": history,
            "knowledge_content": knowledge_content,
        })

        return [BotMessage(text=response)]
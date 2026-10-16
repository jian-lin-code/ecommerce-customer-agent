from knowledge.providers import KnowledgeProvider


class KnowledgeProviderRegistry:
    """
    只是提供者注册表
    """

    def __init__(self, providers: list[KnowledgeProvider]) -> None:

        self._providers_by_id = {p.provider_id: p for p in providers}

    def get(self, provider_id: str) -> KnowledgeProvider:
        return self._providers_by_id[provider_id]
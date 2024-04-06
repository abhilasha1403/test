from typing import Any, List, Optional

from proj.core import LLMClient
from proj.core.awel import MapOperator
from proj.core.awel.task.base import IN
from proj.rag.chunk import Chunk
from proj.rag.retriever.rerank import DefaultRanker
from proj.rag.retriever.rewrite import QueryRewrite


class RerankOperator(MapOperator[Any, Any]):
    """The Rewrite Operator."""

    def __init__(
        self,
        topk: Optional[int] = 3,
        algorithm: Optional[str] = "default",
        rank_fn: Optional[callable] = None,
        **kwargs
    ):
        """Init the query rewrite operator.
        Args:
            topk (int): The number of the candidates.
            algorithm (Optional[str]): The rerank algorithm name.
            rank_fn (Optional[callable]): The rank function.
        """
        super().__init__(**kwargs)
        self._algorithm = algorithm
        self._rerank = DefaultRanker(
            topk=topk,
            rank_fn=rank_fn,
        )

    async def map(self, candidates_with_scores: IN) -> List[Chunk]:
        """rerank the candidates.
        Args:
            candidates_with_scores (IN): The candidates with scores.
        Returns:
            List[Chunk]: The reranked candidates.
        """
        return await self.blocking_func_to_async(
            self._rerank.rank, candidates_with_scores
        )

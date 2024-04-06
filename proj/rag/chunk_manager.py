from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from proj.rag.chunk import Chunk
from proj.rag.extractor.base import Extractor
from proj.rag.knowledge.base import ChunkStrategy, Knowledge


class SplitterType(Enum):
    """splitter type"""

    LANGCHAIN = "langchain"
    LLAMA_INDEX = "llama-index"
    USER_DEFINE = "user_define"


class ChunkParameters(BaseModel):
    """ChunkParameters"""

    chunk_strategy: str = Field(
        default=None,
        description="chunk strategy",
    )
    text_splitter: Optional[Any] = Field(
        default=None,
        description="text splitter",
    )

    splitter_type: SplitterType = Field(
        default=SplitterType.USER_DEFINE,
        description="splitter type",
    )

    chunk_size: int = Field(
        default=512,
        description="chunk size",
    )
    chunk_overlap: int = Field(
        default=50,
        description="chunk overlap",
    )
    separator: str = Field(
        default="\n",
        description="chunk separator",
    )
    enable_merge: bool = Field(
        default=None,
        description="enable chunk merge by chunk_size.",
    )


class ChunkManager:
    """ChunkManager"""

    def __init__(
        self,
        knowledge: Knowledge = None,
        chunk_parameter: Optional[ChunkParameters] = None,
        extractor: Optional[Extractor] = None,
    ):
        """
        Args:
            knowledge: (Knowledge) Knowledge datasource.
            chunk_parameter: (Optional[ChunkParameter]) Chunk parameter.
            extractor: (Optional[Extractor]) Extractor to use for summarization.
        """
        self._knowledge = knowledge

        self._extractor = extractor
        self._chunk_parameters = chunk_parameter or ChunkParameters()
        self._chunk_strategy = (
            chunk_parameter.chunk_strategy
            or self._knowledge.default_chunk_strategy().name
        )
        self._text_splitter = chunk_parameter.text_splitter
        self._splitter_type = chunk_parameter.splitter_type

    def split(self, documents) -> List[Chunk]:
        """Split a document into chunks."""
        text_splitter = self._select_text_splitter()
        if SplitterType.LANGCHAIN == self._splitter_type:
            documents = text_splitter.split_documents(documents)
            return [Chunk.langchain2chunk(document) for document in documents]
        elif SplitterType.LLAMA_INDEX == self._splitter_type:
            nodes = text_splitter.split_text(documents)
            return [Chunk.llamaindex2chunk(node) for node in nodes]
        else:
            return text_splitter.split_documents(documents)

    def split_with_summary(
        self, document: Any, chunk_strategy: ChunkStrategy
    ) -> List[Chunk]:
        """Split a document into chunks and summary"""

        raise NotImplementedError

    @property
    def chunk_parameters(self) -> ChunkParameters:
        return self._chunk_parameters

    def set_text_splitter(
        self,
        text_splitter,
        splitter_type: Optional[SplitterType] = SplitterType.LANGCHAIN,
    ) -> None:
        """Add text splitter."""
        self._text_splitter = text_splitter
        self._splitter_type = splitter_type

    def get_text_splitter(
        self,
    ) -> Any:
        """get text splitter."""
        return self._select_text_splitter()

    def _select_text_splitter(
        self,
    ):
        """Select text splitter by chunk strategy."""
        if self._text_splitter:
            return self._text_splitter
        if not self._chunk_strategy or "Automatic" == self._chunk_strategy:
            self._chunk_strategy = self._knowledge.default_chunk_strategy().name
        if self._chunk_strategy not in [
            support_chunk_strategy.name
            for support_chunk_strategy in self._knowledge.support_chunk_strategy()
        ]:
            current_type = self._knowledge.type().value
            if self._knowledge.document_type():
                current_type = self._knowledge.document_type().value
            raise ValueError(
                f"{current_type} knowledge not supported chunk strategy {self._chunk_strategy} "
            )
        strategy = ChunkStrategy[self._chunk_strategy]
        return strategy.match(
            chunk_size=self._chunk_parameters.chunk_size,
            chunk_overlap=self._chunk_parameters.chunk_overlap,
            separator=self._chunk_parameters.separator,
            enable_merge=self._chunk_parameters.enable_merge,
        )

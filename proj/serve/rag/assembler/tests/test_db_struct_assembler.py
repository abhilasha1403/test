from unittest.mock import MagicMock

import pytest

from proj.datasource.rdbms.conn_sqlite import SQLiteTempConnect
from proj.rag.chunk_manager import ChunkParameters, SplitterType
from proj.rag.embedding.embedding_factory import EmbeddingFactory
from proj.rag.knowledge.base import Knowledge
from proj.rag.text_splitter.text_splitter import CharacterTextSplitter
from proj.serve.rag.assembler.embedding import EmbeddingAssembler
from proj.storage.vector_store.connector import VectorStoreConnector


@pytest.fixture
def mock_db_connection():
    """Create a temporary database connection for testing."""
    connect = SQLiteTempConnect.create_temporary_db()
    connect.create_temp_tables(
        {
            "user": {
                "columns": {
                    "id": "INTEGER PRIMARY KEY",
                    "name": "TEXT",
                    "age": "INTEGER",
                },
                "data": [
                    (1, "Tom", 10),
                    (2, "Jerry", 16),
                    (3, "Jack", 18),
                    (4, "Alice", 20),
                    (5, "Bob", 22),
                ],
            }
        }
    )
    return connect


@pytest.fixture
def mock_chunk_parameters():
    return MagicMock(spec=ChunkParameters)


@pytest.fixture
def mock_embedding_factory():
    return MagicMock(spec=EmbeddingFactory)


@pytest.fixture
def mock_vector_store_connector():
    return MagicMock(spec=VectorStoreConnector)


@pytest.fixture
def mock_knowledge():
    return MagicMock(spec=Knowledge)


def test_load_knowledge(
    mock_db_connection,
    mock_knowledge,
    mock_chunk_parameters,
    mock_embedding_factory,
    mock_vector_store_connector,
):
    mock_chunk_parameters.chunk_strategy = "CHUNK_BY_SIZE"
    mock_chunk_parameters.text_splitter = CharacterTextSplitter()
    mock_chunk_parameters.splitter_type = SplitterType.USER_DEFINE
    assembler = EmbeddingAssembler(
        knowledge=mock_knowledge,
        chunk_parameters=mock_chunk_parameters,
        embedding_factory=mock_embedding_factory,
        vector_store_connector=mock_vector_store_connector,
    )
    assembler.load_knowledge(knowledge=mock_knowledge)
    assert len(assembler._chunks) == 0

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def sample_state():
    """A minimal ProjectState-like dictionary for testing."""
    return {
        'current_phase': 'planning',
        'requirements': 'Build a REST API',
        'specs': '',
        'human_answer': '',
        'clarification_question': '',
        'pending_tasks': [],
        'workspace_files': {},
        'current_task_index': 0,
        'current_task': '',
        'review_feedback': '',
        'test_results': '',
        'revision_count': 0,
        'total_revisions': 0,
        'final_report': '',
        'integration_bugs': [],
        'communication_log': [],
    }

@pytest.fixture
def sample_workspace_files():
    return {
        'src/main.py': 'print("hello")',
        'tests/test_main.py': 'def test_main(): pass',
    }

@pytest.fixture
def sample_task():
    return {
        'task_name': 'Create User Model',
        'user_story': 'As a developer, I want a User model.',
        'acceptance_criteria': ['User has name', 'User has email'],
    }

@pytest.fixture
def mock_llm_factory():
    factory = MagicMock()
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"specs": "test specs"}'))
    factory.create.return_value = mock_llm
    return factory

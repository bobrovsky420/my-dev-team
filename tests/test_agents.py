from unittest.mock import patch
from devteam.agents.code_reviewer import CodeReviewer
from devteam.agents.developer import SeniorDeveloper
from devteam.agents.product_manager import ProductManager
from devteam.agents.qa_engineer import QAEngineer
from devteam.agents.qa_final import FinalQAEngineer
from devteam.agents.reporter import Reporter
from devteam.agents.system_architect import SystemArchitect

from devteam.agents.schemas import (
    CodeReviewerResponse,
    DeveloperResponse,
    WorkspaceFile,
    QAEngineerResponse,
    FinalQAResponse,
)

# --- Helpers ---

def make_config(role="TestAgent", required_inputs=None):
    return {
        "role": role,
        "name": role.lower().replace(" ", "_"),
        "model": "reasoning",
        "temperature": 0.2,
        "required_inputs": required_inputs or [],
    }

# --- CodeReviewer Tests ---

class TestCodeReviewer:
    def test_build_inputs_with_workspace(self, sample_workspace_files):
        config = make_config("Code Reviewer", ["specs", "current_task"])
        agent = CodeReviewer(config, "prompt {specs} {current_task} {workspace}", "reviewer")
        state = {
            "specs": "spec",
            "current_task": "task",
            "workspace_files": sample_workspace_files,
        }
        inputs = agent._build_inputs(state)
        assert "--- FILE: src/main.py ---" in inputs["workspace"]
        assert "--- FILE: tests/test_main.py ---" in inputs["workspace"]

    def test_build_inputs_no_workspace(self):
        config = make_config("Code Reviewer", [])
        agent = CodeReviewer(config, "prompt {workspace}", "reviewer")
        state = {"workspace_files": {}}
        inputs = agent._build_inputs(state)
        assert "No files exist" in inputs["workspace"]

    def test_update_state_approved(self):
        config = make_config("Code Reviewer")
        agent = CodeReviewer(config, "prompt", "reviewer")
        parsed = CodeReviewerResponse(review_feedback="APPROVED")
        result = agent._update_state(parsed, {})
        assert result["review_feedback"] == "APPROVED"
        assert "APPROVED" in result["communication_log"][0]

    def test_update_state_with_changes(self):
        config = make_config("Code Reviewer")
        agent = CodeReviewer(config, "prompt", "reviewer")
        parsed = CodeReviewerResponse(review_feedback="- [main.py] - Bug: missing import")
        result = agent._update_state(parsed, {})
        assert result["review_feedback"] == "- [main.py] - Bug: missing import"
        assert "REQUESTED CHANGES" in result["communication_log"][0]

    def test_update_state_approved_with_dots(self):
        config = make_config("Code Reviewer")
        agent = CodeReviewer(config, "prompt", "reviewer")
        parsed = CodeReviewerResponse(review_feedback="  APPROVED.  ")
        result = agent._update_state(parsed, {})
        assert result["review_feedback"] == "APPROVED"

# --- SeniorDeveloper Tests ---

class TestSeniorDeveloper:
    def test_workspace_file_normalizes_fully_escaped_newlines(self):
        file_obj = WorkspaceFile(
            path="tests/test_user_input.py",
            content="import unittest\\n\\nfrom user_input import parse_number\\n",
        )
        assert "\\n" not in file_obj.content
        assert "import unittest\n\nfrom user_input import parse_number\n" == file_obj.content

    def test_workspace_file_preserves_normal_multiline_content(self):
        content = "def add(a, b):\n    return a + b\n"
        file_obj = WorkspaceFile(path="calculator.py", content=content)
        assert file_obj.content == content

    def test_workspace_file_normalizes_heavily_escaped_mixed_content(self):
        content = "'''Doc'''\\n\\ndef parse_number(x):\n    return float(x)\\n"
        file_obj = WorkspaceFile(path="user_input.py", content=content)
        assert "\\n\\n" not in file_obj.content
        assert "'''Doc'''\n\ndef parse_number(x):\n    return float(x)\n" == file_obj.content

    def test_build_inputs_no_workspace(self):
        config = make_config("Developer", ["specs", "current_task"])
        agent = SeniorDeveloper(config, "prompt {specs} {current_task} {workspace}", "developer")
        state = {"specs": "spec", "current_task": "build it", "workspace_files": {}}
        inputs = agent._build_inputs(state)
        assert "No files exist yet" in inputs["workspace"]

    def test_build_inputs_with_workspace_and_feedback(self, sample_workspace_files):
        config = make_config("Developer", ["specs", "current_task"])
        agent = SeniorDeveloper(config, "prompt {specs} {current_task} {workspace}", "developer")
        state = {
            "specs": "spec",
            "current_task": "task",
            "workspace_files": sample_workspace_files,
            "review_feedback": "Fix the import",
            "test_results": "FAILED: edge case",
        }
        inputs = agent._build_inputs(state)
        assert "--- FILE: src/main.py ---" in inputs["workspace"]
        assert "ACTIVE BUG REPORTS" in inputs["workspace"]
        assert "review_feedback" in inputs["workspace"]
        assert "test_results" in inputs["workspace"]

    def test_update_state_new_files(self):
        config = make_config("Developer")
        agent = SeniorDeveloper(config, "prompt", "developer")
        parsed = DeveloperResponse(workspace_files=[
            WorkspaceFile(path="src/app.py", content="app code"),
            WorkspaceFile(path="tests/test_app.py", content="test code"),
        ])
        current_state = {"workspace_files": {}, "revision_count": 0}
        result = agent._update_state(parsed, current_state)
        assert "src/app.py" in result["workspace_files"]
        assert "tests/test_app.py" in result["workspace_files"]
        assert result["revision_count"] == 0  # First time, not a revision
        assert result["review_feedback"] == ""
        assert result["test_results"] == ""

    def test_update_state_revision(self):
        config = make_config("Developer")
        agent = SeniorDeveloper(config, "prompt", "developer")
        parsed = DeveloperResponse(workspace_files=[
            WorkspaceFile(path="src/app.py", content="fixed code"),
        ])
        current_state = {
            "workspace_files": {"src/app.py": "old code"},
            "revision_count": 1,
            "review_feedback": "Fix bug",
        }
        result = agent._update_state(parsed, current_state)
        assert result["workspace_files"]["src/app.py"] == "fixed code"
        assert result["revision_count"] == 2  # Incremented because review_feedback exists

    def test_update_state_merges_workspace(self):
        config = make_config("Developer")
        agent = SeniorDeveloper(config, "prompt", "developer")
        parsed = DeveloperResponse(workspace_files=[
            WorkspaceFile(path="new.py", content="new file"),
        ])
        current_state = {
            "workspace_files": {"old.py": "old code"},
            "revision_count": 0,
        }
        result = agent._update_state(parsed, current_state)
        assert "old.py" in result["workspace_files"]
        assert "new.py" in result["workspace_files"]

# --- ProductManager Tests ---

class TestProductManager:
    def test_has_correct_schema(self):
        from devteam.agents.schemas import ProductManagerResponse
        config = make_config("Product Manager")
        agent = ProductManager(config, "prompt", "pm")
        assert agent.output_schema is ProductManagerResponse

# --- QAEngineer Tests ---

class TestQAEngineer:
    def test_build_inputs_with_workspace(self, sample_workspace_files):
        config = make_config("QA Engineer", ["specs", "current_task"])
        agent = QAEngineer(config, "prompt {specs} {current_task} {workspace}", "qa")
        state = {
            "specs": "spec",
            "current_task": "task",
            "workspace_files": sample_workspace_files,
        }
        inputs = agent._build_inputs(state)
        assert "--- FILE: src/main.py ---" in inputs["workspace"]

    def test_build_inputs_empty_workspace(self):
        config = make_config("QA Engineer", [])
        agent = QAEngineer(config, "prompt {workspace}", "qa")
        state = {"workspace_files": {}}
        inputs = agent._build_inputs(state)
        assert "No files exist" in inputs["workspace"]

    def test_update_state_passed(self):
        config = make_config("QA Engineer")
        agent = QAEngineer(config, "prompt", "qa")
        parsed = QAEngineerResponse(test_results="PASSED")
        result = agent._update_state(parsed, {})
        assert result["test_results"] == "APPROVED"
        assert "APPROVED" in result["communication_log"][0]

    def test_update_state_bugs(self):
        config = make_config("QA Engineer")
        agent = QAEngineer(config, "prompt", "qa")
        parsed = QAEngineerResponse(test_results="Bug found: missing null check")
        result = agent._update_state(parsed, {})
        assert result["test_results"] == "Bug found: missing null check"
        assert "BUGS FOUND" in result["communication_log"][0]

# --- FinalQAEngineer Tests ---

class TestFinalQAEngineer:
    def test_build_inputs_with_workspace(self, sample_workspace_files):
        config = make_config("Final QA", ["specs"])
        agent = FinalQAEngineer(config, "prompt {specs} {workspace}", "final_qa")
        state = {"specs": "spec", "workspace_files": sample_workspace_files}
        inputs = agent._build_inputs(state)
        assert "--- FILE: src/main.py ---" in inputs["workspace"]

    def test_update_state_passed(self):
        config = make_config("Final QA")
        agent = FinalQAEngineer(config, "prompt", "final_qa")
        parsed = FinalQAResponse(evaluation_summary="All good", test_results="PASSED")
        result = agent._update_state(parsed, {})
        assert result["test_results"] == "APPROVED"
        assert "APPROVED" in result["communication_log"][0]

    def test_update_state_bugs_sets_integration_task(self):
        config = make_config("Final QA")
        agent = FinalQAEngineer(config, "prompt", "final_qa")
        parsed = FinalQAResponse(evaluation_summary="Issues found", test_results="Integration bug in auth")
        result = agent._update_state(parsed, {})
        assert result["test_results"] == "Integration bug in auth"
        assert "FINAL INTEGRATION" in result["current_task"]
        assert result["revision_count"] == 0

# --- Reporter Tests ---

class TestReporter:
    def test_build_inputs_with_workspace(self, sample_workspace_files):
        config = make_config("Reporter", ["specs"])
        agent = Reporter(config, "prompt {specs} {workspace} {history}", "reporter")
        state = {
            "specs": "spec",
            "workspace_files": sample_workspace_files,
            "communication_log": ["Log entry 1", "Log entry 2"],
        }
        inputs = agent._build_inputs(state)
        assert "--- FILE: src/main.py ---" in inputs["workspace"]
        assert "Log entry 1" in inputs["history"]
        assert "Log entry 2" in inputs["history"]

    def test_build_inputs_empty_workspace(self):
        config = make_config("Reporter", [])
        agent = Reporter(config, "prompt {workspace} {history}", "reporter")
        state = {"workspace_files": {}, "communication_log": []}
        inputs = agent._build_inputs(state)
        assert "No files were generated" in inputs["workspace"]

# --- SystemArchitect Tests ---

class TestSystemArchitect:
    def test_has_correct_schema(self):
        from devteam.agents.schemas import SystemArchitectResponse
        config = make_config("System Architect")
        agent = SystemArchitect(config, "prompt", "architect")
        assert agent.output_schema is SystemArchitectResponse

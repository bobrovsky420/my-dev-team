from pathlib import Path
from devteam.tools import DockerSandbox
from devteam.utils.status import is_approved_status
from .schemas import ApproveCode, QAEngineerResponse, ReportIssues
from .base_agent import BaseAgent

class QAEngineer(BaseAgent[QAEngineerResponse]):
    output_schema = QAEngineerResponse
    tools = [ApproveCode, ReportIssues]
    sandbox: DockerSandbox = None

    def _build_inputs(self, state: dict) -> dict:
        inputs = super()._build_inputs(state)
        workspace_str = ''
        if workspace_files := state.get('workspace_files', {}):
            for filepath, content in workspace_files.items():
                clean_content = self.sanitize_for_prompt(content, [filepath, 'workspace'])
                workspace_str += f"--- FILE: {filepath} ---\n{clean_content}\n\n"
            if self.sandbox:
                test_results = self._run_tests(state)
                inputs['test_results'] = self.sanitize_for_prompt(test_results, ['test_results'])
        else:
            workspace_str = "No files exist in the workspace."
        inputs['workspace'] = workspace_str.strip()
        return inputs

    def _run_tests(self, state: dict) -> str:
        target_runtime = state.get('runtime', 'auto')
        workspace_path = Path(state['workspace_path'])
        self.logger.info("🐳 Running tests in Docker Sandbox...")
        test_results = self.sandbox.run_tests(workspace_path, runtime=target_runtime)
        self.logger.debug("Sandbox Output:\n%s", test_results)
        return test_results

    def _map_tool_to_output(self, tool_name: str, tool_args: dict) -> QAEngineerResponse:
        if tool_name == 'ApproveCode':
            return QAEngineerResponse(test_results='PASSED')
        if tool_name == 'ReportIssues':
            return QAEngineerResponse(test_results=tool_args['feedback'])
        raise ValueError(f"Unexpected tool call: {tool_name}")

    def _update_state(self, parsed_data: QAEngineerResponse, current_state: dict) -> dict:
        results = parsed_data.test_results
        if is_approved_status(results):
            results = 'APPROVED'
        status = 'APPROVED' if results == 'APPROVED' else 'BUGS FOUND'
        return {
            'test_results': results,
            'communication_log': [f"**[{self.name or self.role}]:** {status}\n{results}"]
        }

    def with_sandbox(self, sandbox: DockerSandbox):
        self.sandbox = sandbox
        return self

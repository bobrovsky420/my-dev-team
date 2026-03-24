import logging
from typing import Any
from langgraph.graph import StateGraph, START, END
from devteam.state import ProjectState
from devteam.utils import task_to_markdown
from devteam.utils.status import is_approved_status

class ProjectManager:
    role = 'Project Manager'
    max_revision_count: int = 3

    def __init__(self, agents: dict):
        self.logger = logging.getLogger(self.role)
        self.agents = agents

    def build_graph(self, memory: Any = None) -> StateGraph:
        agents = self.agents
        workflow = StateGraph(ProjectState)

        # Planning nodes
        workflow.add_node('human', self.dummy_human_node)
        workflow.add_node('pm', agents['pm'].process)
        workflow.add_node('architect', agents['architect'].process)

        # Task routing
        workflow.add_node('manager', self.route_tasks_node)

        # Development nodes
        workflow.add_node('developer', agents['developer'].process)
        workflow.add_node('reviewer', agents['reviewer'].process)
        workflow.add_node('qa', agents['qa'].process)

        # Integration nodes
        workflow.add_node('final_qa', agents['final_qa'].process)
        workflow.add_node('reporter', agents['reporter'].process)

        # Planning edges
        workflow.add_conditional_edges(START, self.route_planning)
        workflow.add_conditional_edges('human', self.route_planning)
        workflow.add_conditional_edges('pm', self.route_planning)
        workflow.add_conditional_edges('architect', self.route_after_planning)

        # Task routing edges
        workflow.add_conditional_edges('manager', self.edge_from_router)

        # Development edges
        workflow.add_edge('developer', 'reviewer')
        workflow.add_conditional_edges('reviewer', self.route_reviewer)
        workflow.add_conditional_edges('qa', self.route_qa)

        # Integration edges
        workflow.add_conditional_edges('final_qa', self.route_final_qa)
        workflow.add_edge('reporter', END)

        return workflow.compile(checkpointer=memory, interrupt_before=['human'])

    # Planning routing

    def dummy_human_node(self, state: dict) -> dict:
        self.logger.debug("Human input received. Resuming workflow...")
        return {'clarification_question': ''}

    def route_planning(self, state: dict) -> str:
        if state.get('abort_requested'):
            return END
        if state.get('clarification_question'):
            return 'human'
        if not state.get('specs'):
            return 'pm'
        if not state.get('pending_tasks'):
            return 'architect'
        return 'manager'

    def route_after_planning(self, state: dict) -> str:
        if state.get('abort_requested'):
            self.logger.debug("Stopping lifecycle graph after planning abort.")
            return END
        if not state.get('pending_tasks'):
            self.logger.debug("No backlog pending, stopping lifecycle graph")
            return END
        return 'manager'

    # Task routing

    def route_tasks_node(self, state: dict) -> dict:
        pending = state.get('pending_tasks', [])
        idx = state.get('current_task_index', 0)
        current_revisions = state.get('revision_count', 0)
        if idx < len(pending):
            task = pending[idx]
            t_name = task.get('task_name', f'Task {idx+1}')
            formatted_task = task_to_markdown(task, idx + 1)
            self.logger.info("Routing to Task %i/%i: %s", idx + 1, len(pending), t_name)
            return {
                'current_phase': 'development',
                'current_task': formatted_task,
                'current_task_index': idx + 1,
                'total_revisions': current_revisions, # Pass task revisions to total aggregator
                'revision_count': 0,                  # Reset loop counter for new task
                'review_feedback': '',
                'test_results': '',
                'communication_log': [f"\n### Task {idx + 1}: {t_name} ###"]
            }
        self.logger.info("Execution phase completed. Routing to integration.")
        return {
            'current_phase': 'integration',
            'current_task': '',
            'total_revisions': current_revisions,
        }

    def edge_from_router(self, state: dict) -> str:
        if state.get('abort_requested'):
            return END
        phase = state.get('current_phase')
        if phase == 'development':
            return 'developer'
        if phase == 'integration':
            return 'final_qa'
        return END

    # Development routing

    def route_reviewer(self, state: dict) -> str:
        feedback = state.get('review_feedback', '')
        if is_approved_status(feedback):
            return 'qa'
        if state.get('revision_count', 0) >= self.max_revision_count:
            self.logger.warning("Max revisions reached. Forcing completion.")
            return 'manager'
        return 'developer'

    def route_qa(self, state: dict) -> str:
        results = state.get('test_results', '')
        if is_approved_status(results):
            self.logger.debug("Task '%s' passed all checks!", state.get('current_task'))
            return 'manager'
        if state.get('revision_count', 0) >= self.max_revision_count:
            self.logger.warning("Max revisions reached. Forcing completion.")
            return 'manager'
        return 'developer'

    # Integration routing

    def route_final_qa(self, state: dict) -> str:
        results = state.get('test_results', '')
        if is_approved_status(results):
            self.logger.debug("Integration tests passed. Proceeding to reporter.")
            return 'reporter'
        self.logger.error("Integration bugs found! Halting release.")
        return END

from .base_extension import CrewExtension

class ConsoleLogger(CrewExtension):
    def on_start(self, thread_id: str, state: dict):
        print(f"\n🚀 [STARTING THREAD: {thread_id}]")
        if 'requirements' in state and 'pending_tasks' not in state:
            print("Phase: 📋 Planning (Backlog Creation)")
        elif 'current_task' in state:
            print(f"Phase: 💻 Execution (Task: {state.get('current_task')})")
        elif 'code' in state and 'final_report' in state:
            print("Phase: 📦 Release & Integration")

    def on_step(self, thread_id: str, *, state_update: dict, full_state: dict):
        logs = full_state.get('communication_log', [])
        if logs:
            latest_log = logs[-1]
            print(f"  ➜ {latest_log.splitlines()[0]}")

    def on_pause(self, thread_id: str, state: dict, next_node: str) -> dict | None:
        print(f"\n⏸️  [PAUSED] Waiting on: {next_node}")
        if next_node == 'human':
            user_input = input("Enter your feedback (or press Enter to approve): ")
            return {'clarification_question': '', 'human_answer': user_input}
        return None

    def on_finish(self, thread_id: str, final_state: dict):
        print(f"✅ [FINISHED THREAD: {thread_id}]\n")
        if tasks := final_state.get('pending_tasks'):
            print(f"Generated {len(tasks)} tasks for the backlog.")
        elif code := final_state.get('code'):
            print(f"Code updated. Revisions took: {final_state.get('revision_count', 0)}")
        elif report := final_state.get('final_report'):
            print("Release report generated successfully.")

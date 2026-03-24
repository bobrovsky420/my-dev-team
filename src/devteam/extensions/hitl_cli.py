from .base_extension import CrewExtension

class HumanInTheLoop(CrewExtension):
    """Extension that pauses the workflow to get human input at the 'human' node."""

    @staticmethod
    def needs_human_input(current_state: dict, next_node: str) -> bool:
        return bool(current_state.get('clarification_question')) or next_node == 'human'

    def on_pause(self, thread_id: str, current_state: dict, next_node: str) -> dict | None:
        if not self.needs_human_input(current_state, next_node):
            return None
        question = current_state.get('clarification_question', 'The team needs your input.')
        print("\n" + "="*50)
        print("🛑 THE CREW NEEDS YOUR INPUT")
        print("="*50)
        print(f"Question: {question}\n")
        user_input = input("Your Answer (or type 'exit' to abort): ")
        if user_input.lower() in ['exit', 'quit']:
            print("Aborting project...")
            return {
                'abort_requested': True,
                'communication_log': ["**[Human]**: Aborted the workflow."]
            }
        return {
            'human_answer': user_input,
            'communication_log': [f"**[Human]**: {user_input}"]
        }

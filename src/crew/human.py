from .extension import CrewExtension

class HumanInTheLoop(CrewExtension):
    """Extension that pauses the workflow to get human input at the 'human' node."""

    def on_pause(self, thread_id: str, current_state: dict, next_node: str) -> dict | None:
        if next_node == 'human':
            question = current_state.get('clarification_question')
            print("\n" + "="*50)
            print("🛑 THE CREW NEEDS YOUR INPUT")
            print("="*50)
            print(f"Question: {question}\n")
            user_input = input("Your Answer (or type 'exit' to abort): ")
            if user_input.lower() in ['exit', 'quit']:
                print("Aborting project...")
                exit(0)
            return {
                'human_answer': user_input,
                'communication_log': [f"**[Human]**: {user_input}"]
            }
        return None

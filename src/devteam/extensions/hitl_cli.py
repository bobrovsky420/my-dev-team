from langchain_core.messages import HumanMessage
from .base_extension import CrewExtension

class HumanInTheLoop(CrewExtension):
    """Extension that pauses the workflow to get human input at the 'human' node."""

    def on_pause(self, thread_id: str, current_state: dict, next_node: str) -> dict | None:
        if next_node != 'human':
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
                'communication_log': self.communication("Aborted the workflow.")
            }
        return {
            'messages': [HumanMessage(content=user_input)],
            'communication_log': self.communication(user_input)
        }

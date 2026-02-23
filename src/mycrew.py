from dotenv import load_dotenv
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents import get_llm
from agents import ProductManager, SeniorDeveloper, CodeReviewer, QAEngineer, CrewManager
from project import ProjectState

load_dotenv()

LOG_FILE = 'mycrew.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def build_crew_graph():
    # 1. Initialize LLM and Agents
    llm = get_llm(model_name="qwen3:8b") # Change to your preferred local model

    pm = ProductManager(llm)
    dev = SeniorDeveloper(llm)
    reviewer = CodeReviewer(llm)
    qa = QAEngineer(llm)
    manager = CrewManager(llm)

    # 2. Initialize State Graph
    workflow = StateGraph(ProjectState)

    # 3. Add Nodes (Wrapper functions to match LangGraph signature)
    workflow.add_node("manager", manager.process)
    workflow.add_node("pm", pm.process)
    workflow.add_node("developer", dev.process)
    workflow.add_node("reviewer", reviewer.process)
    workflow.add_node("qa", qa.process)

    # 4. Define Routing Function
    def router(state: ProjectState) -> str:
        next_agent = state.get("next_agent")
        if next_agent == "FINISH":
            return END
        return next_agent

    # 5. Add Edges
    # The manager is the entry point and the router for every cycle
    workflow.set_entry_point("manager")

    # After any agent does their work, it goes back to the Crew Manager to decide the next step
    workflow.add_edge("pm", "manager")
    workflow.add_edge("developer", "manager")
    workflow.add_edge("reviewer", "manager")
    workflow.add_edge("qa", "manager")

    # The Manager node uses conditional edges based on the router function
    workflow.add_conditional_edges(
        "manager",
        router,
        {
            "pm": "pm",
            "developer": "developer",
            "reviewer": "reviewer",
            "qa": "qa",
            END: END
        }
    )

    # Add memory checkpointer
    memory = MemorySaver()

    # Compile with memory
    return workflow.compile(checkpointer=memory)

if __name__ == '__main__':
    # Stakeholder requirements
    initial_requirements = (
        "Build a Python CLI application that accepts a URL, scrapes the text content "
        "from the webpage, and saves it to a local text file. It should handle exceptions gracefully."
    )

    # Initialize State
    initial_state = {
        "requirements": initial_requirements,
        "specs": "",
        "code": "",
        "review_feedback": "",
        "test_results": "",
        "revision_count": 0,
        "next_agent": "",
        "project_status": "started"
    }

    # Run the virtual crew
    app = build_crew_graph()

    # Define a configuration with a thread_id
    config = {"configurable": {"thread_id": "project_alpha"}}

    print(f"Starting Project Requirements: {initial_requirements}\n")

    # Execute graph with the config
    for output in app.stream(initial_state, config):
        pass

    # NOW this will work perfectly!
    final_state = app.get_state(config).values

    print("\n\n" + "="*50)
    print("PROJECT COMPLETED")
    print("="*50)

    final_code = final_state.get("code", "No code generated")
    print("FINAL CODE:")
    print(final_code)

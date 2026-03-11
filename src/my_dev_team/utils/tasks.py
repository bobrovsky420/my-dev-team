
def task_to_markdown(task, idx: int) -> str:
    t_name = task.get('task_name', f'Task {idx}')
    t_story = task.get('user_story', '')
    t_criteria = task.get('acceptance_criteria', [])
    acc_criteria = '\n'.join([f'- {c}' for c in t_criteria])
    return (
        f"## {t_name}\n\n"
        f"**User Story:**\n{t_story}\n\n"
        f"**Acceptance Criteria:**\n{acc_criteria}\n\n"
    )

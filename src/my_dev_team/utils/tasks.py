
def task_to_markdown(task, idx: int) -> str:
    t_name = task.get('task_name', '')
    t_full_name = t_name if t_name.lower().startswith('task') else f'Task {idx}: {t_name}'
    t_story = task.get('user_story', '')
    t_criteria = task.get('acceptance_criteria', [])
    acc_criteria = '\n'.join([f'- {c}' for c in t_criteria])
    return (
        f"## {t_full_name}\n\n"
        f"### User Story\n\n{t_story}\n\n"
        f"### Acceptance Criteria\n\n{acc_criteria}\n\n"
    )

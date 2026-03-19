from typing import Any
from langgraph.graph import END

class History:
    """Mixin for show history functionality."""

    app: Any # type: ignore

    async def get_history(self, thread_id: str) -> list[dict]:
        config = {'configurable': {'thread_id': thread_id}}
        all_checkpoints = []
        seen_c_ids = set()
        async for state_snapshot in self.app.aget_state_history(config):
            c_id = state_snapshot.config['configurable']['checkpoint_id']
            if c_id not in seen_c_ids:
                all_checkpoints.append({
                    'time': state_snapshot.created_at,
                    'ns': 'root',
                    'c_id': c_id,
                    'node': state_snapshot.next[0] if state_snapshot.next else END
                })
                seen_c_ids.add(c_id)
            full_state = await self.app.aget_state(state_snapshot.config, subgraphs=True)
            for task in full_state.tasks:
                if task.state and hasattr(task.state, 'config'):
                    sub_ns = task.state.config['configurable'].get('checkpoint_ns')
                    if sub_ns:
                        sub_config = {
                            'configurable': {
                                'thread_id': thread_id,
                                'checkpoint_ns': sub_ns
                            }
                        }
                        async for sub_snapshot in self.app.aget_state_history(sub_config):
                            sub_c_id = sub_snapshot.config['configurable']['checkpoint_id']
                            if sub_c_id not in seen_c_ids:
                                all_checkpoints.append({
                                    'time': sub_snapshot.created_at,
                                    'ns': sub_ns,
                                    'c_id': sub_c_id,
                                    'node': sub_snapshot.next[0] if sub_snapshot.next else END
                                })
                                seen_c_ids.add(sub_c_id)
        all_checkpoints.sort(key=lambda x: x['time'], reverse=True)
        return all_checkpoints

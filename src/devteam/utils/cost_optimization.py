from typing import Any, Dict, List

class CostOptimization:
    call_history: List[Dict[str, Any]]
    agent_calls: Dict[str, int]

    def generate_optimization_report(self):
        print("\n" + "="*40)
        print("🔍 TOKEN OPTIMIZATION DIAGNOSTICS")
        print("="*40)
        warnings = []

        # 1. Detect Thrashing (too many loops for one agent)
        for agent, count in self.agent_calls.items():
            if count > 5:
                warnings.append(f"⚠️  Thrashing Detected: `{agent}` was called {count} times. The agent might be stuck in a failure loop.")

        # 2. Detect Context Bloat (Input tokens growing exponentially)
        for agent in set([c['agent'] for c in self.call_history]):
            agent_calls = [c for c in self.call_history if c['agent'] == agent]
            if len(agent_calls) > 2:
                first_input = agent_calls[0]['input_tokens']
                last_input = agent_calls[-1]['input_tokens']
                if first_input > 0 and (last_input / first_input) > 2.5:
                    warnings.append(f"📈 Context Bloat: `{agent}` input grew by {(last_input/first_input):.1f}x (Started: {first_input}, Ended: {last_input}).")

        # 3. Detect High Waste Ratio (Massive input, tiny output)
        waste_flagged = False
        for call in self.call_history:
            if call['input_tokens'] > 5000 and call['output_tokens'] < 50 and not waste_flagged:
                warnings.append(f"🗑️  High Waste Ratio: `{call['agent']}` received {call['input']} tokens but only generated {call['output']} tokens.")
                waste_flagged = True

        if warnings:
            for w in warnings:
                print(w)
        else:
            print("✅ No major token leakage detected. Highly efficient run!")
        print("="*40 + "\n")

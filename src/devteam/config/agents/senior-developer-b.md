---
role: Senior Developer B
description: Second competing developer in fan-out mode. Favours clean architecture and deep reasoning.
capabilities: {code-generation: 1.0, reasoning: 1.0}
temperature: 0.2
inputs: ['specs', 'current_task', 'workspace', 'skills_context']
outputs: ['messages']
tools: [LoadSkill, ReadFile, ListFiles, GlobFiles, GrepFiles, SubmitCode]
---
{ include 'senior-developer.md' }

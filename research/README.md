# Research Notes: Harness Engineering

This folder collects working research for a future "harness engineering for data analysis" course.

Files:

- `openai-harness-engineering.md`: distilled notes from OpenAI's article.
- `symphony-repository.md`: notes from the `openai/symphony` repository, its spec, and the Elixir reference implementation.
- `data-analysis-harness-design.md`: application of those ideas to this project's target stack.

Primary sources used:

- OpenAI article, "Harness engineering: leveraging Codex in an agent-first world" (February 11, 2026): https://openai.com/index/harness-engineering/
- `openai/symphony` repository: https://github.com/openai/symphony
- Symphony spec: https://github.com/openai/symphony/blob/main/SPEC.md
- Symphony Elixir README: https://github.com/openai/symphony/blob/main/elixir/README.md

Working interpretation:

- Harness engineering is not "prompt engineering for a coding model."
- It is the engineering work required to make agent execution reliable: repository structure, feedback loops, guardrails, workflows, observability, and cleanup.
- Symphony is best read as an orchestration layer that assumes harness engineering already exists in the target repository.

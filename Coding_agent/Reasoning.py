from . import providers

SYSTEM = """You are a senior software architect. Given a user's request and their project context, produce a detailed solution plan.

Your plan must include:
1. Architecture / approach — what pattern, libraries, structure
2. Files needed — what files to create or modify and why
3. Key implementation details — important logic, edge cases, data flow
4. Dependencies — any packages, imports, or external services

Focus on clarity, correctness, and professional-grade code.
Think step by step. If the user wants an edit to existing code, analyze the current code first and plan minimal changes."""


def run(intent: dict, session: dict) -> dict:
    project = session.get("project", {})
    files = project.get("files", {})
    tech_stack = intent.get("tech_stack") or project.get("tech_stack") or []

    parts = [f"Task: {intent.get('summary', '')}"]
    parts.append(f"Intent type: {intent.get('intent', 'new_project')}")
    if tech_stack:
        parts.append(f"Tech stack: {', '.join(tech_stack)}")

    if files:
        parts.append("\nCurrent project files:")
        for path, content in files.items():
            preview = content[:500] if len(content) > 500 else content
            parts.append(f"\n--- {path} ---\n{preview}")

    if intent.get("clarifying_questions"):
        parts.append(f"\nClarifications needed: {' '.join(intent['clarifying_questions'])}")

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "\n".join(parts)}
    ]

    models = providers.get_models()
    provider_name, model = models["reasoning"]

    plan = providers.query(provider_name, model, messages, temperature=0.3)

    return {
        "plan": plan,
        "tech_stack": tech_stack,
    }

import json
import os
from . import providers
from . import knowledge

SYSTEM = """You are an expert software engineer generating production-ready code. Given a solution plan, generate complete, working files.

Output ONLY a JSON object with this structure:
{
  "files": {
    "path/to/file1.js": "full file content here",
    "path/to/file2.py": "full file content here"
  },
  "root_dir": "suggested_project_name"
}

Rules:
- Generate complete, working files — never snippets or placeholders
- Follow language/framework best practices and conventions
- Include proper imports, error handling, and edge cases
- Use modern syntax and idiomatic patterns
- Generate all files needed for a working project
- Code must be production-quality and secure"""


def run(plan: dict, session: dict) -> dict:
    tech_stack = plan.get("tech_stack", [])
    knowledge_context = knowledge.get_context(tech_stack)

    parts = [f"Solution plan:\n{plan.get('plan', '')}"]
    if knowledge_context:
        parts.append(f"\nReference patterns:\n{knowledge_context}")
    parts.append("\nGenerate complete, working code files. Output JSON only.")

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "\n".join(parts)}
    ]

    models = providers.get_models()
    provider_name, model = models["code_gen"]

    try:
        result = providers.query(provider_name, model, messages, temperature=0.2)
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(result)

        root_dir = data.get("root_dir", "project")
        files = data.get("files", {})

        return {
            "files": files,
            "root_dir": root_dir,
        }
    except Exception as e:
        return {
            "files": {},
            "root_dir": "project",
            "error": str(e)
        }

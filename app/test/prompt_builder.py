from __future__ import annotations

from typing import Any, Dict, List

from app.test.compact_lesson_context import compact_context_from_lesson


def _bullet_lines(items: List[str], prefix: str = "- ") -> str:
    return "\n".join(f"{prefix}{x}" for x in items if x and str(x).strip())


def build_system_prompt(ctx: Dict[str, Any]) -> str:
    lesson = ctx.get("lesson") or {}
    title = str(lesson.get("title") or "").strip()
    level = str(lesson.get("level") or "").strip()
    agenda = lesson.get("agenda") or []

    vocabulary = ctx.get("vocabulary") or []
    patterns = ctx.get("patterns") or []
    common_errors = ctx.get("common_errors") or []
    starters = ctx.get("conversation_starters") or []

    # Ограничения для компактности промпта
    max_agenda = 8
    max_vocab = 12
    max_patterns = 12
    max_errors = 8
    max_starters = 8

    # --- Vocabulary formatting
    vocab_lines: List[str] = []
    for v in vocabulary[:max_vocab]:
        term = str(v.get("term") or "").strip()
        if not term:
            continue
        definition = (str(v.get("definition")).strip() if v.get("definition") is not None else "")
        example = (str(v.get("example")).strip() if v.get("example") is not None else "")

        line = f"- {term}"
        if definition:
            line += f" — {definition}"
        if example:
            line += f" (example: {example})"
        vocab_lines.append(line)

    # --- Patterns
    pattern_lines = [f"- {p.strip()}" for p in patterns[:max_patterns] if isinstance(p, str) and p.strip()]

    # --- Errors
    error_lines: List[str] = []
    for e in common_errors[:max_errors]:
        wrong = str(e.get("wrong") or "").strip()
        right = str(e.get("right") or "").strip()
        if wrong and right:
            error_lines.append(f'- "{wrong}" -> "{right}"')

    # --- Starters
    starter_lines = [f"- {s.strip()}" for s in starters[:max_starters] if isinstance(s, str) and s.strip()]

    # --- Goals (agenda)
    goals_lines = [f"- {x}" for x in agenda[:max_agenda] if isinstance(x, str) and x.strip()]

    prompt = f"""You are an English tutor ({level}). Keep the conversation natural and friendly.
When the user writes in English:
- correct up to 1–3 key mistakes (briefly),
- provide 1 short tip,
- ask 1 follow-up question to continue.
Prefer vocabulary and patterns from the lesson context.

LESSON CONTEXT
Title: {title} ({level})
Goals:
{_bullet_lines(goals_lines) if goals_lines else "- (no goals provided)"}

Vocabulary (use actively):
{chr(10).join(vocab_lines) if vocab_lines else "- (no vocabulary provided)"}

Useful patterns:
{chr(10).join(pattern_lines) if pattern_lines else "- (no patterns provided)"}

Common mistakes to watch:
{chr(10).join(error_lines) if error_lines else "- (no common errors provided)"}

Conversation starters:
{chr(10).join(starter_lines) if starter_lines else "- (no starters provided)"}
""".strip()

    return prompt


def build_system_prompt_from_lesson():
    ctx = compact_context_from_lesson()
    system_prompt = build_system_prompt(ctx)

    assert "LESSON CONTEXT" in system_prompt
    assert "Vocabulary" in system_prompt

    print(system_prompt)

build_system_prompt_from_lesson()
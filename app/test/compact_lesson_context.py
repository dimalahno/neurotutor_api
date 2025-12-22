import json
from logging import Logger
from pathlib import Path

logger = Logger(__name__)

def _unique_keep_order(items):
    seen = set()
    out = []
    for x in items:
        if not x:
            continue
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def extract_compact_context(lesson: dict) -> dict:
    lesson_id = str(lesson.get("slug") or lesson.get("id") or "")
    title = str(lesson.get("title") or "")
    lang_level = lesson.get("lang_level")
    if isinstance(lang_level, list):
        level = "/".join([str(x) for x in lang_level if x is not None])
    else:
        level = str(lang_level or "")

    # agenda
    agenda = []
    agenda_raw = lesson.get("agenda") or {}
    if isinstance(agenda_raw, dict):
        tmp = []
        for k, v in agenda_raw.items():
            if isinstance(v, dict):
                order_id = int(v.get("order_id") or 10_000)
                desc = str(v.get("description") or k)
                tmp.append((order_id, f"{k}: {desc}" if desc and desc != k else str(k)))
            else:
                tmp.append((10_000, str(k)))
        tmp.sort(key=lambda x: x[0])
        agenda = [x[1] for x in tmp]

    # units
    units_raw = lesson.get("units") or []
    units = []
    for unit in units_raw if isinstance(units_raw, list) else []:
        if not isinstance(unit, dict):
            continue
        units.append(
            {
                "id": str(unit.get("id") or ""),
                "title": str(unit.get("title") or ""),
                "type": str(unit.get("type") or ""),
            }
        )

    # vocabulary
    vocabulary = []
    for unit in units_raw if isinstance(units_raw, list) else []:
        if not isinstance(unit, dict) or unit.get("type") != "vocabulary":
            continue
        for activity in unit.get("activities") or []:
            if not isinstance(activity, dict) or activity.get("type") != "vocab_list":
                continue
            for w in activity.get("words") or []:
                if not isinstance(w, dict):
                    continue
                term = str(w.get("term") or "").strip()
                if not term:
                    continue
                vocabulary.append(
                    {
                        "term": term,
                        "definition": (str(w.get("definition")) if w.get("definition") is not None else None),
                        "example": (str(w.get("example")) if w.get("example") is not None else None),
                    }
                )
        break

    vocab_terms = [v["term"] for v in vocabulary]

    patterns = []
    conversation_starters = []
    keywords = []
    common_errors = []
    writing_guidelines = []

    def consume_question(q: dict):
        prompt = str(q.get("prompt") or "").strip()
        if prompt:
            conversation_starters.append(prompt)
        for pattern in q.get("targetPatterns") or []:
            if isinstance(pattern, str) and pattern.strip():
                patterns.append(pattern.strip())
        for keyword in q.get("keywords") or []:
            if isinstance(keyword, str) and keyword.strip():
                keywords.append(keyword.strip())

    for unit in units_raw if isinstance(units_raw, list) else []:
        if not isinstance(unit, dict):
            continue

        for activity in unit.get("activities") or []:
            if not isinstance(activity, dict):
                continue

            a_type = activity.get("type")

            if a_type == "speaking_prompt":
                for question in activity.get("questions") or []:
                    if isinstance(question, dict):
                        consume_question(question)

            if a_type == "roleplay":
                for t in activity.get("turns") or []:
                    if not isinstance(t, dict):
                        continue
                    if t.get("type") == "question":
                        text = str(t.get("text") or "").strip()
                        if text:
                            conversation_starters.append(text)
                    for p in t.get("targetPatterns") or []:
                        if isinstance(p, str) and p.strip():
                            patterns.append(p.strip())
                    for kw in t.get("keywords") or []:
                        if isinstance(kw, str) and kw.strip():
                            keywords.append(kw.strip())

            if a_type == "error_correction":
                for it in activity.get("items") or []:
                    if not isinstance(it, dict):
                        continue
                    wrong = str(it.get("sentence") or "").strip()
                    right = str(it.get("correct") or "").strip()
                    if wrong and right:
                        common_errors.append({"wrong": wrong, "right": right})

            if unit.get("type") == "writing" and a_type == "open_answer":
                gl = activity.get("guidelines")
                if isinstance(gl, list) and gl:
                    for g in gl:
                        if isinstance(g, str) and g.strip():
                            writing_guidelines.append(g.strip())
                else:
                    p = str(activity.get("prompt") or "").strip()
                    if p:
                        writing_guidelines.append(p)

    return {
        "lesson": {
            "id": lesson_id,
            "title": title,
            "level": level,
            "agenda": agenda,
        },
        "units": units,
        "vocabulary": vocabulary,
        "patterns": _unique_keep_order(patterns),
        "common_errors": common_errors,
        "conversation_starters": _unique_keep_order(conversation_starters)[:20],
        "writing_guidelines": _unique_keep_order(writing_guidelines)[:20],
        "keywords": _unique_keep_order(vocab_terms + keywords)[:40],
    }


def compact_context_from_lesson():
    path = Path("../../init_data/lesson_1.json")
    lesson = json.loads(path.read_text(encoding="utf-8"))

    ctx = extract_compact_context(lesson)

    logger.info(json.dumps(ctx, ensure_ascii=False, indent=2))
    return ctx

compact_context_from_lesson()
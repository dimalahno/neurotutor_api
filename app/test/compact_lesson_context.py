from logging import Logger
from typing import List, Dict, Any, Optional

logger = Logger(__name__)

def _unique_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in items:
        if not x:
            continue
        x = str(x).strip()
        if not x or x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def _take_first(items: List[Any], limit: int) -> List[Any]:
    return items[:limit] if isinstance(items, list) else []


def extract_compact_context(lesson: dict) -> dict:
    # --- basic meta ---
    lesson_id = str(lesson.get("slug") or lesson.get("_id") or lesson.get("id") or "")
    title = str(lesson.get("title") or "")

    lang_level = lesson.get("lang_level")
    if isinstance(lang_level, list):
        level = "/".join([str(x) for x in lang_level if x is not None])
    else:
        level = str(lang_level or "")

    # --- agenda ---
    agenda: List[str] = []
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

    units_raw = lesson.get("units") or []
    units: List[Dict[str, Any]] = []
    if isinstance(units_raw, list):
        for unit in units_raw:
            if not isinstance(unit, dict):
                continue
            units.append(
                {
                    "id": str(unit.get("id") or ""),
                    "title": str(unit.get("title") or ""),
                    "type": str(unit.get("type") or ""),
                    "order": unit.get("order"),
                }
            )

    # --- collectors ---
    patterns: List[str] = []
    conversation_starters: List[str] = []
    keywords: List[str] = []
    common_errors: List[Dict[str, str]] = []
    writing_guidelines: List[str] = []
    vocabulary: List[Dict[str, Optional[str]]] = []

    reading_ctx: Optional[Dict[str, Any]] = None
    grammar_ctx: Optional[Dict[str, Any]] = None
    pronunciation_ctx: Optional[Dict[str, Any]] = None
    speaking_ctx: Optional[Dict[str, Any]] = None
    writing_ctx: Optional[Dict[str, Any]] = None

    def consume_question(q: dict):
        prompt = str(q.get("prompt") or "").strip()
        if prompt:
            conversation_starters.append(prompt)
        for pattern in q.get("targetPatterns") or []:
            if isinstance(pattern, str) and pattern.strip():
                patterns.append(pattern.strip())
        for kw in q.get("keywords") or []:
            if isinstance(kw, str) and kw.strip():
                keywords.append(kw.strip())

    # --- parse units ---
    for unit in units_raw if isinstance(units_raw, list) else []:
        if not isinstance(unit, dict):
            continue

        u_type = unit.get("type")
        activities = unit.get("activities") or []

        # vocabulary (берём первое vocab_list)
        if u_type == "vocabulary" and not vocabulary:
            for activity in activities:
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

        # reading (сжато: title + description + professions + glossary)
        if u_type == "reading" and reading_ctx is None:
            rd = unit.get("reading") or {}
            if isinstance(rd, dict):
                text = (rd.get("text") or {}) if isinstance(rd.get("text"), dict) else {}
                content_data = text.get("content_data") or []
                professions: List[str] = []
                if isinstance(content_data, list):
                    for it in content_data:
                        if isinstance(it, dict):
                            p = str(it.get("profession") or "").strip()
                            if p:
                                professions.append(p)

                glossary = rd.get("glossary") or []
                gloss_small = []
                if isinstance(glossary, list):
                    for g in glossary:
                        if not isinstance(g, dict):
                            continue
                        w = str(g.get("word") or "").strip()
                        d = str(g.get("definition") or "").strip()
                        if w:
                            gloss_small.append({"word": w, "definition": d or None})
                            keywords.append(w)

                desc = str(text.get("description") or "").strip()
                reading_ctx = {
                    "title": str(rd.get("title") or "").strip() or str(unit.get("title") or "").strip(),
                    "description": desc or None,
                    "professions": _unique_keep_order(professions)[:10],
                    "glossary": _take_first(gloss_small, 10),
                }
                keywords.extend(professions)

        # grammar (rule + examples)
        if u_type == "grammar" and grammar_ctx is None:
            expl = unit.get("explanation") or {}
            if isinstance(expl, dict):
                examples = expl.get("examples") or []
                grammar_ctx = {
                    "rule": str(expl.get("text") or "").strip() or None,
                    "examples": [str(x).strip() for x in examples if isinstance(x, str) and x.strip()][:6],
                }

        # pronunciation (слова + транскрипции)
        if u_type == "pronunciation" and pronunciation_ctx is None:
            words_out = []
            for activity in activities:
                if not isinstance(activity, dict) or activity.get("type") != "listen_and_repeat":
                    continue
                for w in activity.get("words") or []:
                    if not isinstance(w, dict):
                        continue
                    term = str(w.get("term") or "").strip()
                    tr = str(w.get("transcript") or "").strip()
                    if term:
                        words_out.append({"term": term, "transcript": tr or None})
                        keywords.append(term)
                break
            if words_out:
                pronunciation_ctx = {"words": words_out[:20]}

        # writing (prompt + guidelines)
        if u_type == "writing" and writing_ctx is None:
            for activity in activities:
                if not isinstance(activity, dict) or activity.get("type") != "open_answer":
                    continue
                prompt = str(activity.get("prompt") or "").strip()
                gl = activity.get("guidelines")
                gl_out: List[str] = []
                if isinstance(gl, list):
                    gl_out = [str(x).strip() for x in gl if isinstance(x, str) and x.strip()]
                writing_ctx = {
                    "prompt": prompt or None,
                    "guidelines": gl_out[:10],
                }
                writing_guidelines.extend(gl_out)
                if prompt:
                    writing_guidelines.append(prompt)
                break

        # activities scan for patterns/starters/keywords/errors + roleplay tutor questions
        for activity in activities if isinstance(activities, list) else []:
            if not isinstance(activity, dict):
                continue

            a_type = activity.get("type")

            if a_type == "speaking_prompt":
                for question in activity.get("questions") or []:
                    if isinstance(question, dict):
                        consume_question(question)

            if a_type == "roleplay":
                rp_prompt = str(activity.get("prompt") or "").strip()
                tutor_questions: List[str] = []
                for t in activity.get("turns") or []:
                    if not isinstance(t, dict):
                        continue
                    if t.get("type") == "question":
                        text = str(t.get("text") or "").strip()
                        if text:
                            tutor_questions.append(text)
                            conversation_starters.append(text)

                    # patterns/keywords обычно на answer-turn'ах
                    for p in t.get("targetPatterns") or []:
                        if isinstance(p, str) and p.strip():
                            patterns.append(p.strip())
                    for kw in t.get("keywords") or []:
                        if isinstance(kw, str) and kw.strip():
                            keywords.append(kw.strip())

                if speaking_ctx is None and (rp_prompt or tutor_questions):
                    speaking_ctx = {
                        "roleplay_prompt": rp_prompt or None,
                        "tutor_questions": _unique_keep_order(tutor_questions)[:10],
                    }

            if a_type == "error_correction":
                for it in activity.get("items") or []:
                    if not isinstance(it, dict):
                        continue
                    wrong = str(it.get("sentence") or "").strip()
                    right = str(it.get("correct") or "").strip()
                    if wrong and right:
                        common_errors.append({"wrong": wrong, "right": right})

    vocab_terms = [v["term"] for v in vocabulary if v.get("term")]

    ctx = {
        "lesson": {
            "id": lesson_id,
            "title": title,
            "level": level,
            "agenda": agenda,
        },
        "units": units,
        "vocabulary": _take_first(vocabulary, 30),
        "reading": reading_ctx,
        "grammar": grammar_ctx,
        "pronunciation": pronunciation_ctx,
        "speaking": speaking_ctx,
        "writing": writing_ctx,
        "patterns": _unique_keep_order(patterns)[:40],
        "common_errors": _take_first(common_errors, 30),
        "conversation_starters": _unique_keep_order(conversation_starters)[:25],
        "writing_guidelines": _unique_keep_order(writing_guidelines)[:20],
        "keywords": _unique_keep_order(vocab_terms + keywords)[:60],
    }
    return ctx
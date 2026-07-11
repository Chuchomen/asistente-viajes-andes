import json
import re
import unicodedata
from pathlib import Path


KNOWLEDGE_PATH = Path(__file__).with_name("knowledge_base.json")
STOPWORDS = {
    "a",
    "al",
    "con",
    "cuanto",
    "de",
    "del",
    "el",
    "en",
    "la",
    "las",
    "lo",
    "los",
    "para",
    "por",
    "que",
    "si",
    "tienen",
    "un",
    "una",
    "viaje",
    "viajes",
}


def normalize(text):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9\s]", " ", text)


def load_knowledge_base(path=KNOWLEDGE_PATH):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def retrieve_context(question, knowledge_base=None, max_items=3):
    knowledge_base = knowledge_base or load_knowledge_base()
    normalized_question = normalize(question)
    question_words = {
        word
        for word in normalized_question.split()
        if len(word) > 2 and word not in STOPWORDS
    }
    scored_items = []

    for item in knowledge_base:
        keywords = {normalize(keyword) for keyword in item["keywords"]}
        keyword_score = sum(2 for keyword in keywords if keyword in normalized_question)
        text_words = set(normalize(f"{item['title']} {item['answer']}").split())
        overlap_score = len(question_words.intersection(text_words))
        score = keyword_score + overlap_score

        if keyword_score > 0 or score >= 3:
            scored_items.append({**item, "score": score})

    scored_items.sort(key=lambda item: item["score"], reverse=True)
    return scored_items[:max_items]


def build_context_block(items):
    if not items:
        return ""

    context_lines = []
    for item in items:
        context_lines.append(
            f"- {item['title']} ({item['category']}): {item['answer']}"
        )
    return "\n".join(context_lines)


def build_full_knowledge_block(knowledge_base=None):
    knowledge_base = knowledge_base or load_knowledge_base()
    lines = []
    for item in knowledge_base:
        lines.append(f"- {item['title']} ({item['category']}): {item['answer']}")
    return "\n".join(lines)


def fallback_answer():
    return (
        "No tengo ese dato en la base de conocimiento de Viajes Andes. "
        "Para no inventarte informacion, te recomiendo escribir al WhatsApp "
        "310 245 7788 y un asesor lo confirma contigo."
    )

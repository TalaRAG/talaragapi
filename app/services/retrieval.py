import re


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def build_context(query, documents, limit=5):
    query_tokens = _tokens(query)
    if not query_tokens:
        return "", []

    scored_chunks = []
    for document in documents:
        for chunk in _chunk_document(document):
            score = _score_chunk(query_tokens, chunk["content"])
            if score <= 0:
                continue
            scored_chunks.append(
                {
                    "score": score,
                    "document": document,
                    "content": chunk["content"],
                }
            )

    scored_chunks.sort(key=lambda entry: entry["score"], reverse=True)
    top_chunks = scored_chunks[: max(limit, 1)]
    if not top_chunks:
        return "", []

    context_parts = []
    matched_documents = []
    seen_ids = set()
    for entry in top_chunks:
        document = entry["document"]
        context_parts.append(
            (
                f"Document: {document.name}\n"
                f"Type: {document.document_type or 'unknown'}\n"
                f"Content:\n{entry['content']}"
            )
        )
        if document.id not in seen_ids:
            matched_documents.append(document)
            seen_ids.add(document.id)

    return "\n\n---\n\n".join(context_parts), matched_documents


def _chunk_document(document, chunk_size=1200, overlap=200):
    text = (document.extracted_text or "").strip()
    if not text:
        return []

    chunks = []
    cursor = 0
    while cursor < len(text):
        end = min(len(text), cursor + chunk_size)
        content = text[cursor:end].strip()
        if content:
            chunks.append({"content": content})
        if end >= len(text):
            break
        cursor = max(end - overlap, cursor + 1)
    return chunks


def _tokens(value):
    return TOKEN_PATTERN.findall((value or "").lower())


def _score_chunk(query_tokens, content):
    content_tokens = set(_tokens(content))
    if not content_tokens:
        return 0
    token_overlap = sum(1 for token in query_tokens if token in content_tokens)
    if token_overlap == 0:
        return 0
    phrase_bonus = 2 if " ".join(query_tokens) in (content or "").lower() else 0
    return token_overlap + phrase_bonus

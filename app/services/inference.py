import httpx


_llama_instance = None
_llama_model_path = None


def generate_answer(*, settings, prompt):
    provider = (settings.INFERENCE_PROVIDER or "openai").lower()
    if provider == "openai":
        return _generate_openai_answer(settings=settings, prompt=prompt)
    if provider == "local":
        return _generate_local_answer(settings=settings, prompt=prompt)
    raise ValueError(f"Unsupported INFERENCE_PROVIDER: {settings.INFERENCE_PROVIDER}")


def iter_text_chunks(text, chunk_size):
    text = text or ""
    step = max(int(chunk_size or 1), 1)
    for index in range(0, len(text), step):
        yield text[index : index + step]


def _generate_openai_answer(*, settings, prompt):
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY must be set when INFERENCE_PROVIDER=openai")

    url = settings.OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
    with httpx.Client(timeout=settings.OPENAI_TIMEOUT_SECONDS) as client:
        response = client.post(
            url,
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": settings.INFERENCE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
        )
        response.raise_for_status()
        payload = response.json()

    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    if isinstance(content, list):
        return "".join(
            part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"
        )
    return content


def _generate_local_answer(*, settings, prompt):
    llm = _get_llama(settings)
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": settings.INFERENCE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=settings.LLAMA_CPP_TEMPERATURE,
        max_tokens=settings.LLAMA_CPP_MAX_TOKENS,
    )
    return response["choices"][0]["message"]["content"]


def _get_llama(settings):
    global _llama_instance, _llama_model_path

    if not settings.LLAMA_CPP_MODEL_PATH:
        raise ValueError("LLAMA_CPP_MODEL_PATH must be set when INFERENCE_PROVIDER=local")

    if _llama_instance is not None and _llama_model_path == settings.LLAMA_CPP_MODEL_PATH:
        return _llama_instance

    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise ValueError("llama-cpp-python must be installed when INFERENCE_PROVIDER=local") from exc

    kwargs = {
        "model_path": settings.LLAMA_CPP_MODEL_PATH,
        "n_ctx": settings.LLAMA_CPP_N_CTX,
        "n_threads": settings.LLAMA_CPP_N_THREADS,
        "n_gpu_layers": settings.LLAMA_CPP_N_GPU_LAYERS,
    }
    if settings.LLAMA_CPP_CHAT_FORMAT:
        kwargs["chat_format"] = settings.LLAMA_CPP_CHAT_FORMAT

    _llama_instance = Llama(**kwargs)
    _llama_model_path = settings.LLAMA_CPP_MODEL_PATH
    return _llama_instance

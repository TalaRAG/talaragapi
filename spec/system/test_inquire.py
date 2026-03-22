def test_inquire_returns_generated_answer(client, document, monkeypatch):
    from app.services.inference import generate_answer

    def fake_generate_answer(*, settings, prompt):
        assert "Budget allocation for health and education." in prompt
        return "The budget prioritizes health and education."

    monkeypatch.setattr("app.services.inference.generate_answer", fake_generate_answer)

    response = client.post(
        "/inquire",
        json={
            "query": "What does the budget prioritize?",
            "document_types": ["national_budget"],
            "k": 5,
        },
    )

    assert response.status_code == 200
    assert response.text == "The budget prioritizes health and education."

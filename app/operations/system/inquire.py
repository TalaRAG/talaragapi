from sqlalchemy import select

from app.models.document import Document
from app.operations.validator import Validator
from app.services import inference
from app.services.retrieval import build_context


class Inquire(Validator):
    def __init__(self, session, settings, query=None, document_types=None, k=None):
        super().__init__()
        self.session = session
        self.settings = settings
        self.query = query
        self.document_types = document_types or []
        self.k = k or settings.INFERENCE_TOP_K_DEFAULT
        self.answer = ""
        self.payload = {"query": [], "document_types": [], "message": []}

    def execute(self):
        self._validate()
        if self.invalid():
            return

        statement = select(Document).where(Document.has_embeddings.is_(True))
        if self.document_types:
            statement = statement.where(Document.document_type.in_(self.document_types))

        documents = self.session.execute(statement.order_by(Document.created_at.desc())).scalars().all()
        context, matched_documents = build_context(self.query, documents, limit=self.k)
        if not context:
            self.answer = (
                "I could not find relevant document content for that question. "
                "Try selecting other document types or uploading more source material."
            )
            return

        prompt = self._build_prompt(context, matched_documents)
        self.answer = inference.generate_answer(settings=self.settings, prompt=prompt)

    def _validate(self):
        if not self.query or not self.query.strip():
            self.payload["query"].append("required")

        invalid_types = [doc_type for doc_type in self.document_types if doc_type not in self.settings.DOCUMENT_TYPES]
        if invalid_types:
            self.payload["document_types"].append("invalid value")

        if self.k <= 0:
            self.payload["message"].append("k must be greater than zero")

        self.count_errors()

    def _build_prompt(self, context, matched_documents):
        source_lines = [
            f"- {document.name} ({document.document_type or 'unknown'})"
            for document in matched_documents
        ]
        sources = "\n".join(source_lines)
        return (
            f"Question:\n{self.query.strip()}\n\n"
            f"Available sources:\n{sources}\n\n"
            f"Context:\n{context}\n\n"
            "Answer the question using only the supplied context. "
            "If the answer is incomplete or unavailable, say so plainly."
        )

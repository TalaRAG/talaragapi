from app.models.document import DOCUMENT_STATUSES, Document
from app.operations.validator import Validator
from app.services.document_extractor import extract_text
from app.storage import delete_file, store_file


class Save(Validator):
    def __init__(
        self,
        session,
        settings,
        name=None,
        description=None,
        document_type=None,
        status=None,
        file=None,
        document=None,
    ):
        super().__init__()
        self.session = session
        self.settings = settings
        self.name = name
        self.description = description
        self.document_type = document_type
        self.status = status
        self.file = file
        self.document = document
        self.payload = {
            "name": [],
            "description": [],
            "document_type": [],
            "status": [],
            "file": [],
            "message": [],
        }

    def execute(self):
        self._validate()
        if self.invalid():
            return

        if self.document is None:
            self.document = Document(
                name=self.name.strip(),
                description=self._normalize_optional_text(self.description),
                document_type=self._normalize_optional_text(self.document_type),
                status=self._normalized_status(),
                original_filename="",
                content_type=None,
                size_bytes=None,
                storage_provider=self.settings.STORAGE_SERVICE,
                storage_key="",
                extracted_text="",
                has_embeddings=False,
            )
            self.session.add(self.document)
        else:
            self.document.name = self.name.strip()
            self.document.description = self._normalize_optional_text(self.description)
            self.document.document_type = self._normalize_optional_text(self.document_type)
            self.document.status = self._normalized_status()

        if self.file is not None:
            previous_key = self.document.storage_key
            result = store_file(self.file, self.settings, filename=self.file.filename)
            self.file.file.seek(0)
            content = self.file.file.read()
            extracted_text = extract_text(self.file.filename, self.file.content_type, content)

            self.document.original_filename = result["filename"]
            self.document.content_type = result["content_type"]
            self.document.size_bytes = result["byte_size"]
            self.document.storage_provider = self.settings.STORAGE_SERVICE
            self.document.storage_key = result["key"]
            self.document.extracted_text = extracted_text.strip()
            self.document.has_embeddings = bool(self.document.extracted_text)

            if previous_key:
                delete_file(previous_key, self.settings)

        self.session.commit()
        self.session.refresh(self.document)

    def _validate(self):
        if not self.name or not self.name.strip():
            self.payload["name"].append("required")

        if self.document is None and self.file is None:
            self.payload["file"].append("required")

        if self.document_type:
            document_type = self.document_type.strip()
            if document_type not in self.settings.DOCUMENT_TYPES:
                self.payload["document_type"].append("invalid value")

        if self.file is not None and not self.file.filename:
            self.payload["file"].append("invalid upload")

        if self.status is not None and self._normalized_status() not in DOCUMENT_STATUSES:
            self.payload["status"].append("invalid value")

        self.count_errors()

    def _normalize_optional_text(self, value):
        if value is None:
            return None
        value = value.strip()
        return value or None

    def _normalized_status(self):
        if self.status is None:
            return "pending"
        return self.status.strip()

import re
from dataclasses import dataclass
from tempfile import SpooledTemporaryFile
from typing import Iterable

from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedPdfMetadata:
    title: str = ""
    authors: str = ""
    journal: str = ""
    conference: str = ""
    year: int | None = None
    doi: str = ""
    abstract: str = ""
    keywords: str = ""


class PdfMetadataExtractor:
    """Extracts deterministic metadata already present in or readable from a PDF."""

    def extract(self, file: SpooledTemporaryFile[bytes]) -> ExtractedPdfMetadata:
        current_position = file.tell()
        file.seek(0)
        try:
            reader = PdfReader(file)
            metadata = reader.metadata or {}
            xmp = getattr(reader, "xmp_metadata", None)
            first_pages_text = self._first_pages_text(reader)
        finally:
            file.seek(current_position)

        title = self._clean(metadata.get("/Title", "") or "")
        authors = self._clean(metadata.get("/Author", "") or "")
        keywords = self._clean(metadata.get("/Keywords", "") or "")
        subject = self._clean(metadata.get("/Subject", "") or "")

        if xmp is not None:
            title = title or self._clean_xmp_value(getattr(xmp, "dc_title", "") or "")
            authors = authors or self._clean_xmp_value(getattr(xmp, "dc_creator", "") or "")
            keywords = keywords or self._clean_xmp_value(getattr(xmp, "pdf_keywords", "") or "")
            subject = subject or self._clean_xmp_value(getattr(xmp, "dc_description", "") or "")

        doi = self._find_doi(first_pages_text) or self._find_doi(subject)
        year = self._find_publication_year(first_pages_text, metadata)
        abstract = subject if len(subject) > 80 else self._find_abstract(first_pages_text)
        title = title or self._find_title(first_pages_text)
        authors = authors or self._find_authors(first_pages_text, title)

        return ExtractedPdfMetadata(
            title=title,
            authors=authors,
            journal=self._find_labeled_value(first_pages_text, "journal"),
            conference=self._find_labeled_value(first_pages_text, "conference"),
            year=year,
            doi=doi,
            abstract=abstract,
            keywords=keywords,
        )

    def _first_pages_text(self, reader: PdfReader, limit: int = 2) -> str:
        chunks: list[str] = []
        for index, page in enumerate(reader.pages):
            if index >= limit:
                break
            try:
                chunks.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(chunks)

    def _find_doi(self, text: str) -> str:
        match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", text, flags=re.IGNORECASE)
        return self._clean(match.group(0)) if match else ""

    def _find_year(self, text: str) -> int | None:
        match = re.search(r"\b((?:19|20)\d{2})\b", text)
        return int(match.group(0)) if match else None

    def _find_publication_year(self, text: str, metadata: object) -> int | None:
        for field in ("year", "published", "publication year", "date"):
            value = self._find_labeled_value(text, field)
            if value:
                year = self._find_year(value)
                if year is not None:
                    return year

        if isinstance(metadata, dict):
            for key in ("/Year", "/PublicationYear", "/Published"):
                year = self._find_year(str(metadata.get(key, "")))
                if year is not None:
                    return year

        return None

    def _find_title(self, text: str) -> str:
        lines = self._candidate_header_lines(text)
        if not lines:
            return ""

        title_lines = [lines[0]]
        if self._looks_like_wrapped_title(lines[0]) and len(lines) > 1:
            title_lines.append(lines[1])

        return self._clean(" ".join(title_lines))

    def _find_authors(self, text: str, title: str) -> str:
        lines = self._candidate_header_lines(text)
        if not lines:
            return ""

        title_words = set(title.split())
        author_lines: list[str] = []
        title_consumed = False

        for line in lines:
            if not title_consumed:
                line_words = set(line.split())
                if line_words and line_words.issubset(title_words):
                    continue
                title_consumed = True

            if self._looks_like_non_author_header(line):
                continue

            normalized = re.sub(r"[*†‡∗]+", "", line).strip()
            if normalized:
                author_lines.append(normalized)

            if len(author_lines) >= 8:
                break

        return self._clean(", ".join(author_lines))

    def _find_abstract(self, text: str) -> str:
        match = re.search(
            r"\babstract\b[:\s]*(.*?)(?=\n\s*(?:keywords|introduction|1\.?\s+introduction)\b)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return ""
        return self._clean(match.group(1))

    def _find_labeled_value(self, text: str, label: str) -> str:
        match = re.search(rf"\b{label}\b\s*:\s*(.+)", text, flags=re.IGNORECASE)
        return self._clean(match.group(1)) if match else ""

    def _clean(self, value: object) -> str:
        if not isinstance(value, str):
            return ""
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    def _clean_xmp_value(self, value: object) -> str:
        if isinstance(value, dict):
            preferred = value.get("x-default") or next(iter(value.values()), "")
            return self._clean_xmp_value(preferred)

        if isinstance(value, str):
            return self._clean(value)

        if isinstance(value, Iterable):
            return self._clean(", ".join(str(item) for item in value if item))

        return ""

    def _candidate_header_lines(self, text: str) -> list[str]:
        before_abstract = re.split(r"\babstract\b", text, maxsplit=1, flags=re.IGNORECASE)[0]
        lines = [self._clean(line) for line in before_abstract.splitlines()]
        return [line for line in lines if line and not self._looks_like_noise(line)]

    def _looks_like_wrapped_title(self, line: str) -> bool:
        return bool(re.search(r"\b(for|of|and|the|with|to|in|from|via)$", line, flags=re.IGNORECASE))

    def _looks_like_noise(self, line: str) -> bool:
        lower = line.lower()
        noise_phrases = (
            "provided proper attribution",
            "google hereby grants permission",
            "reproduce the tables",
            "scholarly works",
            "arxiv:",
        )
        return any(phrase in lower for phrase in noise_phrases)

    def _looks_like_non_author_header(self, line: str) -> bool:
        lower = line.lower()
        if "@" in line or "{" in line or "}" in line:
            return True
        organization_terms = (
            "university",
            "google",
            "research",
            "brain",
            "language",
            "institute",
            "department",
            "school",
            "laboratory",
            "lab",
            "microsoft",
            "facebook",
            "openai",
        )
        return any(term in lower for term in organization_terms)

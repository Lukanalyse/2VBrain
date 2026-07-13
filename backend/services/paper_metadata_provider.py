import json
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class BibliographicMetadata:
    title: str = ""
    authors: str = ""
    journal: str = ""
    conference: str = ""
    year: int | None = None
    doi: str = ""
    abstract: str = ""
    keywords: str = ""
    publisher: str = ""
    source_url: str = ""
    metadata_source: str = "pdf"
    metadata_confidence: str = "low"


class PaperMetadataProvider:
    """Fetch bibliographic metadata from public scholarly sources.

    Network enrichment is best-effort. PDF import should never fail because
    Crossref or OpenAlex is unavailable.
    """

    def enrich(self, local: BibliographicMetadata) -> BibliographicMetadata:
        doi = local.doi.strip()
        if doi:
            for fetcher in (self._fetch_crossref_by_doi, self._fetch_openalex_by_doi):
                remote = fetcher(doi)
                if remote is not None:
                    return self._merge(local, remote)

        if local.title.strip():
            remote = self._fetch_openalex_by_title(local.title)
            if remote is not None:
                return self._merge(local, remote)

        return local

    def _fetch_crossref_by_doi(self, doi: str) -> BibliographicMetadata | None:
        payload = self._read_json(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}")
        message = payload.get("message") if isinstance(payload, dict) else None
        if not isinstance(message, dict):
            return None

        title = self._first(message.get("title"))
        authors = self._crossref_authors(message.get("author"))
        journal = self._first(message.get("container-title"))
        year = self._crossref_year(message)
        abstract = self._clean_abstract(str(message.get("abstract") or ""))
        publisher = str(message.get("publisher") or "")
        source_url = str(message.get("URL") or "")

        return BibliographicMetadata(
            title=title,
            authors=authors,
            journal=journal,
            year=year,
            doi=str(message.get("DOI") or doi),
            abstract=abstract,
            publisher=publisher,
            source_url=source_url,
            metadata_source="crossref",
            metadata_confidence="high",
        )

    def _fetch_openalex_by_doi(self, doi: str) -> BibliographicMetadata | None:
        return self._openalex_work(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}")

    def _fetch_openalex_by_title(self, title: str) -> BibliographicMetadata | None:
        params = urllib.parse.urlencode({"search": title, "per-page": "1"})
        payload = self._read_json(f"https://api.openalex.org/works?{params}")
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list) or not results:
            return None
        work = results[0]
        if not isinstance(work, dict):
            return None
        return self._metadata_from_openalex_work(work, confidence="medium")

    def _openalex_work(self, url: str) -> BibliographicMetadata | None:
        payload = self._read_json(url)
        if not isinstance(payload, dict):
            return None
        return self._metadata_from_openalex_work(payload, confidence="high")

    def _metadata_from_openalex_work(self, work: dict, *, confidence: str) -> BibliographicMetadata:
        host = work.get("primary_location")
        source = host.get("source") if isinstance(host, dict) else None
        concepts = work.get("concepts")
        keywords = ""
        if isinstance(concepts, list):
            keywords = ", ".join(
                str(concept.get("display_name"))
                for concept in concepts[:8]
                if isinstance(concept, dict) and concept.get("display_name")
            )

        return BibliographicMetadata(
            title=str(work.get("title") or ""),
            authors=self._openalex_authors(work.get("authorships")),
            journal=str(source.get("display_name") or "") if isinstance(source, dict) else "",
            year=work.get("publication_year")
            if isinstance(work.get("publication_year"), int)
            else None,
            doi=str(work.get("doi") or "").replace("https://doi.org/", ""),
            abstract=self._openalex_abstract(work.get("abstract_inverted_index")),
            keywords=keywords,
            publisher=str(work.get("publisher") or ""),
            source_url=str(work.get("id") or ""),
            metadata_source="openalex",
            metadata_confidence=confidence,
        )

    def _merge(
        self, local: BibliographicMetadata, remote: BibliographicMetadata
    ) -> BibliographicMetadata:
        return BibliographicMetadata(
            title=remote.title or local.title,
            authors=remote.authors or local.authors,
            journal=remote.journal or local.journal,
            conference=remote.conference or local.conference,
            year=remote.year or local.year,
            doi=remote.doi or local.doi,
            abstract=remote.abstract or local.abstract,
            keywords=remote.keywords or local.keywords,
            publisher=remote.publisher or local.publisher,
            source_url=remote.source_url or local.source_url,
            metadata_source=remote.metadata_source or local.metadata_source,
            metadata_confidence=remote.metadata_confidence or local.metadata_confidence,
        )

    def _read_json(self, url: str) -> dict:
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "ResearchOS/0.1 (mailto:metadata@localhost)",
                },
            )
            with urllib.request.urlopen(request, timeout=4) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            return {}

    def _first(self, value: object) -> str:
        if isinstance(value, list) and value:
            return str(value[0])
        return str(value or "")

    def _crossref_authors(self, value: object) -> str:
        if not isinstance(value, list):
            return ""
        names = []
        for author in value:
            if not isinstance(author, dict):
                continue
            given = str(author.get("given") or "").strip()
            family = str(author.get("family") or "").strip()
            name = " ".join(part for part in (given, family) if part)
            if name:
                names.append(name)
        return ", ".join(names)

    def _crossref_year(self, message: dict) -> int | None:
        for key in ("published-print", "published-online", "published", "issued"):
            date_parts = (
                message.get(key, {}).get("date-parts")
                if isinstance(message.get(key), dict)
                else None
            )
            if (
                isinstance(date_parts, list)
                and date_parts
                and isinstance(date_parts[0], list)
                and date_parts[0]
            ):
                year = date_parts[0][0]
                if isinstance(year, int):
                    return year
        return None

    def _openalex_authors(self, value: object) -> str:
        if not isinstance(value, list):
            return ""
        names = []
        for authorship in value:
            author = authorship.get("author") if isinstance(authorship, dict) else None
            name = author.get("display_name") if isinstance(author, dict) else None
            if name:
                names.append(str(name))
        return ", ".join(names)

    def _openalex_abstract(self, value: object) -> str:
        if not isinstance(value, dict):
            return ""
        words: list[tuple[int, str]] = []
        for word, positions in value.items():
            if not isinstance(positions, list):
                continue
            for position in positions:
                if isinstance(position, int):
                    words.append((position, str(word)))
        return " ".join(word for _, word in sorted(words))

    def _clean_abstract(self, value: str) -> str:
        return (
            value.replace("<jats:p>", "")
            .replace("</jats:p>", "")
            .replace("<p>", "")
            .replace("</p>", "")
            .strip()
        )

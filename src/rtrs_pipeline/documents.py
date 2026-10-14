"""Catálogo, inventário e download resiliente de relatórios RTRS.

Este módulo não presume que o nome legado ``audit_report_rtrsN.pdf`` identifica
uma URL. O inventário local registra essa ausência de vínculo explicitamente.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional
from urllib.parse import urlparse

import requests


PDF_MAGIC = b"%PDF-"
MANIFEST_COLUMNS = [
    "document_id",
    "local_path",
    "file_name",
    "sha256",
    "size_bytes",
    "page_count",
    "pdf_status",
    "native_text_bytes",
    "duplicate_of",
    "source_url",
    "source_linkage",
    "inspected_at_utc",
]
CATALOG_COLUMNS = [
    "catalog_id", "name", "country", "audit_year", "source_url", "url_sha256", "url_duplicate", "cataloged_at_utc"
]


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_probably_pdf(content: bytes) -> bool:
    """Rejeita respostas HTML/erro antes de elas virarem arquivos PDF."""

    return len(content) >= len(PDF_MAGIC) and content.lstrip().startswith(PDF_MAGIC)


def pdf_page_count(path: Path) -> Optional[int]:
    """Obtém páginas via Poppler, sem adicionar dependência Python pesada."""

    try:
        result = subprocess.run(
            ["pdfinfo", str(path)], check=True, capture_output=True, text=True, timeout=30
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def native_text_bytes(path: Path) -> Optional[int]:
    """Mede texto nativo sem persistir uma cópia do conteúdo."""

    try:
        result = subprocess.run(
            ["pdftotext", str(path), "-"], check=True, capture_output=True, timeout=90
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    return len(result.stdout.strip())


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    local_path: str
    file_name: str
    sha256: str
    size_bytes: int
    page_count: Optional[int]
    pdf_status: str
    native_text_bytes: Optional[int]
    duplicate_of: str
    source_url: str
    source_linkage: str
    inspected_at_utc: str


def inventory_pdfs(pdf_dir: Path) -> list[DocumentRecord]:
    """Inspeciona o acervo local e sinaliza duplicatas sem mudar os PDFs."""

    records: list[DocumentRecord] = []
    canonical_by_hash: dict[str, str] = {}
    for path in sorted(pdf_dir.glob("*.pdf")):
        digest = sha256_file(path)
        pages = pdf_page_count(path)
        status = "valid" if pages and pages > 0 else "invalid_or_unreadable"
        canonical = canonical_by_hash.setdefault(digest, path.name)
        records.append(
            DocumentRecord(
                document_id=f"sha256:{digest}",
                local_path=str(path),
                file_name=path.name,
                sha256=digest,
                size_bytes=path.stat().st_size,
                page_count=pages,
                pdf_status=status,
                native_text_bytes=native_text_bytes(path) if status == "valid" else None,
                duplicate_of="" if canonical == path.name else canonical,
                source_url="",
                source_linkage="unlinked_legacy_filename",
                inspected_at_utc=utc_now(),
            )
        )
    return records


def write_csv(path: Path, rows: Iterable[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_document_manifest(pdf_dir: Path, output_path: Path) -> list[DocumentRecord]:
    records = inventory_pdfs(pdf_dir)
    write_csv(output_path, (asdict(record) for record in records), MANIFEST_COLUMNS)
    return records


def write_catalog_manifest(source_csv: Path, output_path: Path) -> int:
    """Normaliza o catálogo RTRS preservando URL e sinalizando URLs repetidas."""

    with source_csv.open(encoding="utf-8", newline="") as handle:
        source = list(csv.DictReader(handle))
    seen_urls: set[str] = set()
    now = utc_now()
    rows = []
    for index, row in enumerate(source, start=1):
        url = (row.get("Links") or "").strip()
        rows.append(
            {
                "catalog_id": f"catalog:{index:04d}",
                "name": (row.get("Names") or "").strip(),
                "country": (row.get("Country") or "").strip(),
                "audit_year": (row.get("Year") or "").strip(),
                "source_url": url,
                "url_sha256": sha256_bytes(url.encode("utf-8")) if url else "",
                "url_duplicate": str(bool(url and url in seen_urls)).lower(),
                "cataloged_at_utc": now,
            }
        )
        if url:
            seen_urls.add(url)
    write_csv(output_path, rows, CATALOG_COLUMNS)
    return len(rows)


class RateLimiter:
    def __init__(self, min_interval_seconds: float) -> None:
        self.min_interval_seconds = min_interval_seconds
        self._lock = threading.Lock()
        self._last_request = 0.0

    def wait(self) -> None:
        with self._lock:
            delay = self.min_interval_seconds - (time.monotonic() - self._last_request)
            if delay > 0:
                time.sleep(delay)
            self._last_request = time.monotonic()


@dataclass(frozen=True)
class DownloadResult:
    source_url: str
    local_path: str
    status: str
    sha256: str = ""
    size_bytes: int = 0
    attempts: int = 0
    error: str = ""


class PdfDownloader:
    """Downloader HTTP com limite de taxa, retentativa, arquivo temporário e retomada."""

    def __init__(
        self,
        output_dir: Path,
        *,
        timeout_seconds: float = 60,
        retries: int = 3,
        backoff_seconds: float = 1.0,
        min_interval_seconds: float = 0.5,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.output_dir = output_dir
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.limiter = RateLimiter(min_interval_seconds)
        self.session = session or requests.Session()

    @staticmethod
    def filename_for_url(url: str) -> str:
        parsed_name = Path(urlparse(url).path).name
        suffix = ".pdf" if not parsed_name.lower().endswith(".pdf") else ""
        url_key = sha256_bytes(url.encode("utf-8"))[:16]
        return f"rtrs_{url_key}{suffix or '.pdf'}"

    def download(self, url: str) -> DownloadResult:
        if not url.lower().startswith(("http://", "https://")):
            return DownloadResult(url, "", "invalid_url", error="URL must use HTTP(S)")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        destination = self.output_dir / self.filename_for_url(url)
        if destination.exists() and pdf_page_count(destination):
            return DownloadResult(url, str(destination), "already_valid", sha256=sha256_file(destination), size_bytes=destination.stat().st_size)

        last_error = ""
        for attempt in range(1, self.retries + 1):
            temporary_path: Optional[Path] = None
            try:
                self.limiter.wait()
                response = self.session.get(url, stream=True, timeout=self.timeout_seconds, headers={"User-Agent": "RTRS-research-reproducibility/1.0"})
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(dir=self.output_dir, suffix=".part", delete=False) as tmp:
                    temporary_path = Path(tmp.name)
                    for chunk in response.iter_content(chunk_size=1024 * 128):
                        if chunk:
                            tmp.write(chunk)
                content_prefix = temporary_path.read_bytes()[:1024]
                if not is_probably_pdf(content_prefix) or not pdf_page_count(temporary_path):
                    raise ValueError("response is not a readable PDF")
                os.replace(temporary_path, destination)
                return DownloadResult(url, str(destination), "downloaded", sha256=sha256_file(destination), size_bytes=destination.stat().st_size, attempts=attempt)
            except (requests.RequestException, OSError, ValueError) as exc:
                last_error = str(exc)
                if temporary_path and temporary_path.exists():
                    temporary_path.unlink()
                if attempt < self.retries:
                    time.sleep(self.backoff_seconds * (2 ** (attempt - 1)))
        return DownloadResult(url, str(destination), "failed", attempts=self.retries, error=last_error)

    def download_many(self, urls: Iterable[str], *, max_workers: int = 2) -> Iterator[DownloadResult]:
        unique_urls = list(dict.fromkeys(url.strip() for url in urls if url and url.strip()))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.download, url) for url in unique_urls]
            for future in as_completed(futures):
                yield future.result()


def write_download_log(results: Iterable[DownloadResult], output_path: Path) -> None:
    rows = [asdict(result) | {"logged_at_utc": utc_now()} for result in results]
    write_csv(output_path, rows, ["source_url", "local_path", "status", "sha256", "size_bytes", "attempts", "error", "logged_at_utc"])

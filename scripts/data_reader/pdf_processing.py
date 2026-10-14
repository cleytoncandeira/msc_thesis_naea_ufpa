"""Conversão de PDFs em imagens (JPEG) para OCR e anotação."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from pdf2image import convert_from_path
from tqdm import tqdm


@dataclass(frozen=True)
class PdfConversionResult:
    """Resumo da conversão de um PDF para imagens."""

    pdf_path: Path
    output_dir: Path
    pages_converted: int
    error: Optional[str] = None


def list_pdf_files(pdf_directory: Path) -> List[Path]:
    """Lista arquivos PDF em um diretório.

    Args:
        pdf_directory: Pasta contendo PDFs.

    Returns:
        Lista ordenada de arquivos com extensão `.pdf`.
    """

    return sorted(p for p in pdf_directory.glob("*.pdf"))


def convert_pdf_to_images(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = 120,
) -> PdfConversionResult:
    """Converte um único PDF em imagens JPEG.

    Args:
        pdf_path: Caminho do PDF.
        output_dir: Diretório de saída para as páginas.
        dpi: Resolução da conversão.

    Example:
        >>> from pathlib import Path
        >>> convert_pdf_to_images(Path("relatorio.pdf"), Path("out/relatorio"), dpi=150)
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        images = convert_from_path(str(pdf_path), dpi=dpi)
    except Exception as exc:
        return PdfConversionResult(pdf_path, output_dir, 0, error=str(exc))

    error: Optional[str] = None
    pages_converted = 0
    for page_number, image in enumerate(
        tqdm(images, desc=f"Processando {pdf_path.name}", unit="página", leave=False),
        start=1,
    ):
        image_path = output_dir / f"page_{page_number}.jpg"
        try:
            image.save(image_path, "JPEG")
        except Exception as exc:
            error = f"Erro ao salvar página {page_number}: {exc}"
            print(f"[ERRO] {pdf_path.name}: {error}")
            continue
        pages_converted += 1

    return PdfConversionResult(pdf_path, output_dir, pages_converted, error=error)


def convert_pdfs_to_images(
    pdf_directory: Path,
    output_directory: Path,
    dpi: int = 120,
) -> List[PdfConversionResult]:
    """Converte todos os PDFs de um diretório em imagens.

    Args:
        pdf_directory: Pasta contendo PDFs.
        output_directory: Pasta onde as imagens serão armazenadas.
        dpi: Resolução da conversão.

    Returns:
        Lista de resultados por PDF.
    """

    output_directory.mkdir(parents=True, exist_ok=True)
    results: List[PdfConversionResult] = []

    for pdf_path in tqdm(list_pdf_files(pdf_directory), desc="Convertendo PDFs", unit="arquivo"):
        pdf_output_dir = output_directory / pdf_path.stem
        result = convert_pdf_to_images(pdf_path, pdf_output_dir, dpi=dpi)
        if result.error:
            print(f"Erro ao processar '{pdf_path.name}': {result.error}")
        results.append(result)

    return results

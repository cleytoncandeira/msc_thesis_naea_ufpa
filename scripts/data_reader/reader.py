"""Script experimental de leitura de PDFs com LayoutLMv2."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from pdf2image import convert_from_path
from PIL import Image
import pytesseract

TokenLabel = Tuple[str, int]

DEFAULT_MODEL_NAME = "microsoft/layoutlmv2-base-uncased"
DEFAULT_DPI = 100


def pdf_to_images(pdf_path: Path, dpi: int = DEFAULT_DPI) -> List[Image.Image]:
    """Converte PDF em imagens PIL."""

    try:
        return convert_from_path(str(pdf_path), dpi=dpi)
    except Exception as exc:
        print(f"Erro ao converter PDF para imagens: {exc}")
        return []


def _extract_words_and_boxes(ocr_data: dict) -> Tuple[List[str], List[List[int]]]:
    words: List[str] = []
    boxes: List[List[int]] = []
    for i, text in enumerate(ocr_data.get("text", [])):
        if not text.strip():
            continue
        words.append(text)
        boxes.append(
            [
                ocr_data["left"][i],
                ocr_data["top"][i],
                ocr_data["left"][i] + ocr_data["width"][i],
                ocr_data["top"][i] + ocr_data["height"][i],
            ]
        )
    return words, boxes


def _normalize_boxes(boxes: List[List[int]], image: Image.Image) -> List[List[int]]:
    width, height = image.size
    normalized: List[List[int]] = []
    for box in boxes:
        normalized.append(
            [
                int(1000 * box[0] / width),
                int(1000 * box[1] / height),
                int(1000 * box[2] / width),
                int(1000 * box[3] / height),
            ]
        )
    return normalized


def load_layoutlmv2(model_name: str = DEFAULT_MODEL_NAME):
    """Carrega o processor e o modelo LayoutLMv2.

    Importa dependências pesadas apenas quando necessário.
    """

    from transformers import LayoutLMv2ForTokenClassification, LayoutLMv2Processor

    processor = LayoutLMv2Processor.from_pretrained(model_name)
    model = LayoutLMv2ForTokenClassification.from_pretrained(model_name)
    return processor, model


def process_page_with_layoutlmv2(image: Image.Image, processor, model) -> List[TokenLabel]:
    """Processa uma imagem com OCR e LayoutLMv2."""

    try:
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        words, boxes = _extract_words_and_boxes(ocr_data)
        normalized_boxes = _normalize_boxes(boxes, image)

        encoding = processor(
            words,
            boxes=normalized_boxes,
            return_tensors="pt",
            truncation=True,
            padding="max_length",
        )

        outputs = model(**encoding)
        logits = outputs.logits

        import torch

        predictions = torch.argmax(logits, dim=2)
        tokens = processor.tokenizer.convert_ids_to_tokens(encoding.input_ids[0])
        labels = predictions[0].tolist()

        return list(zip(tokens, labels))
    except Exception as exc:
        print(f"Erro ao processar página com LayoutLMv2: {exc}")
        return []


def run_demo(
    pdf_path: Path,
    *,
    model_name: str = DEFAULT_MODEL_NAME,
    dpi: int = DEFAULT_DPI,
    query: str = "endereco",
) -> int:
    """Executa um fluxo simples e procura tokens que contenham `query`."""

    processor, model = load_layoutlmv2(model_name)
    images = pdf_to_images(pdf_path, dpi=dpi)

    if not images:
        return 1

    for page_num, image in enumerate(images, start=1):
        results = process_page_with_layoutlmv2(image, processor, model)
        matches = [(token, label) for token, label in results if query.lower() in token.lower()]

        if matches:
            for token, label in matches:
                print(f"Página {page_num}: Token: {token}, Label: {label}")
        else:
            print(f"Página {page_num}: Nenhuma informação relevante encontrada.")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Demo de OCR + LayoutLMv2 em PDFs.")
    parser.add_argument("pdf_path", type=Path, help="Caminho do PDF de entrada.")
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME, help="Nome do modelo LayoutLMv2.")
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI, help="DPI usado para converter o PDF.")
    parser.add_argument("--query", default="endereco", help="Substring para filtrar tokens relevantes.")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    pdf_path = args.pdf_path.expanduser().resolve()
    return run_demo(pdf_path, model_name=args.model_name, dpi=args.dpi, query=args.query)


if __name__ == "__main__":
    raise SystemExit(main())

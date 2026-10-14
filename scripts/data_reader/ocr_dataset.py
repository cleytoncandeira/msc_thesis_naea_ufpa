"""Geração de dataset OCR (JSONL) com labels BIO para relatórios."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, TypedDict

from PIL import Image
import pytesseract

BBox = List[int]


class AnnotationField(TypedDict):
    bbox: BBox
    pagina: str


class RawOcrToken(TypedDict):
    text: str
    bbox: BBox


class LabeledOcrToken(RawOcrToken):
    label: str


def load_json(json_path: Path) -> Dict[str, AnnotationField]:
    """Carrega o JSON de anotações de um relatório."""

    with open(json_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def compute_iou(bbox_a: BBox, bbox_b: BBox) -> float:
    """Calcula IoU (Intersection over Union) entre duas caixas.

    O IoU mede o quanto duas caixas se sobrepõem, variando de 0.0 a 1.0.
    """

    ax1, ay1, ax2, ay2 = bbox_a
    bx1, by1, bx2, by2 = bbox_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0

    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)

    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0

    return inter_area / float(union)


def bbox_center_in(bbox_token: BBox, bbox_field: BBox) -> bool:
    """Verifica se o centro de uma caixa está dentro de outra caixa."""

    tx1, ty1, tx2, ty2 = bbox_token
    fx1, fy1, fx2, fy2 = bbox_field

    cx = (tx1 + tx2) / 2
    cy = (ty1 + ty2) / 2

    return fx1 <= cx <= fx2 and fy1 <= cy <= fy2


def run_ocr_on_image(image_path: Path) -> List[RawOcrToken]:
    """Executa OCR em uma imagem e retorna tokens com bounding boxes."""

    image = Image.open(image_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    tokens: List[RawOcrToken] = []
    for text, conf, left, top, width, height in zip(
        data["text"],
        data["conf"],
        data["left"],
        data["top"],
        data["width"],
        data["height"],
    ):
        text = text.strip()
        try:
            conf_val = float(conf)
        except ValueError:
            conf_val = -1.0
        if not text or conf_val < 0:
            continue

        bbox = [left, top, left + width, top + height]
        tokens.append({"text": text, "bbox": bbox})

    return tokens


def build_dataset_from_reports(
    reports_dir: Path,
    *,
    iou_threshold: float = 0.5,
    use_center: bool = False,
) -> None:
    """Gera um dataset JSONL a partir de relatórios organizados.

    A lógica de associação usa IoU entre o token OCR e o bbox anotado, ou
    opcionalmente o centro do token.
    """

    for company_dir in sorted(reports_dir.iterdir()):
        if not company_dir.is_dir():
            continue
        print(f"== Empresa: {company_dir.name}")

        for report_dir in sorted(company_dir.iterdir()):
            if not report_dir.is_dir():
                continue

            print(f"   >> Relatório: {report_dir.name}")
            json_files = list(report_dir.glob("*.json"))
            if not json_files:
                print(f"   [AVISO] Nenhum JSON encontrado em '{report_dir.name}'. Pulando.")
                continue

            annotations = load_json(json_files[0])
            image_files = sorted(report_dir.glob("*.jpg"))
            if not image_files:
                print(f"   [AVISO] Não há arquivos .jpg em '{report_dir.name}'. Pulando.")
                continue

            ocr_results: Dict[str, List[LabeledOcrToken]] = {}
            for image_path in image_files:
                page_tokens = run_ocr_on_image(image_path)
                labeled_tokens: List[LabeledOcrToken] = [
                    {"text": token["text"], "bbox": token["bbox"], "label": "O"}
                    for token in page_tokens
                ]
                ocr_results[image_path.name] = labeled_tokens

            for field_name, field_info in annotations.items():
                page_name = field_info.get("pagina")
                bbox = field_info.get("bbox")
                if not page_name or not bbox:
                    continue
                if page_name not in ocr_results:
                    print(f"   [AVISO] '{page_name}' não encontrado em '{report_dir.name}'. Pulando '{field_name}'.")
                    continue

                indices: List[int] = []
                for index, token in enumerate(ocr_results[page_name]):
                    token_bbox = token["bbox"]
                    # Atribui rótulos aos tokens que intersectam com o bbox anotado.
                    if use_center:
                        if bbox_center_in(token_bbox, bbox):
                            indices.append(index)
                    else:
                        if compute_iou(token_bbox, bbox) >= iou_threshold:
                            indices.append(index)

                if indices:
                    indices.sort()
                    ocr_results[page_name][indices[0]]["label"] = f"B-{field_name}"
                    for idx in indices[1:]:
                        ocr_results[page_name][idx]["label"] = f"I-{field_name}"

            output_path = report_dir / f"{report_dir.name}_labeled.jsonl"
            with open(output_path, "w", encoding="utf-8") as handle:
                for page_name, tokens in ocr_results.items():
                    for token in tokens:
                        item = {
                            "empresa": company_dir.name,
                            "relatorio": report_dir.name,
                            "pagina": page_name,
                            "text": token["text"],
                            "bbox": token["bbox"],
                            "label": token["label"],
                        }
                        handle.write(json.dumps(item, ensure_ascii=False) + "\n")

            print(f"   [INFO] Dataset anotado salvo em: {output_path}")

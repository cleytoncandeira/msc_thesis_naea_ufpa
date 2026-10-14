"""Ferramentas de anotação manual com OpenCV para relatórios OCR."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Sequence, Tuple, TypedDict

import cv2

BBox = List[int]


class BoxAnnotation(TypedDict):
    bbox: BBox
    label: str


class FieldAnnotation(TypedDict):
    bbox: BBox
    pagina: str


def order_pages_by_index(pages: Iterable[Path]) -> List[Path]:
    """Ordena páginas por número no nome do arquivo."""

    def extract_number(path: Path) -> int:
        match = re.search(r"(\d+)", path.stem)
        return int(match.group(1)) if match else 0

    return sorted(pages, key=extract_number)


def annotate_image(image_path: Path, label: str, scale_percent: int = 50) -> List[BoxAnnotation]:
    """Abre uma imagem e permite desenhar caixas com o mouse.

    Args:
        image_path: Caminho da imagem.
        label: Rótulo associado às caixas desenhadas.
        scale_percent: Percentual de escala usado para exibir a imagem na tela.
    """

    if scale_percent <= 0:
        raise ValueError("scale_percent deve ser maior que zero.")

    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Erro ao carregar a imagem: {image_path}")
        return []

    boxes: List[BBox] = []
    drawing = {"active": False, "start": (0, 0)}

    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    canvas = resized.copy()

    def scale_point(x: int, y: int) -> BBox:
        # Ajusta coordenadas da imagem redimensionada para o tamanho original.
        return [int(x / scale_percent * 100), int(y / scale_percent * 100)]

    def on_mouse(event: int, x: int, y: int, *_args: Tuple[Any, ...]) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing["active"] = True
            drawing["start"] = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and drawing["active"]:
            temp = resized.copy()
            cv2.rectangle(temp, drawing["start"], (x, y), (0, 255, 0), 2)
            cv2.imshow("image", temp)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing["active"] = False
            x_min, y_min = min(drawing["start"][0], x), min(drawing["start"][1], y)
            x_max, y_max = max(drawing["start"][0], x), max(drawing["start"][1], y)
            scaled_min = scale_point(x_min, y_min)
            scaled_max = scale_point(x_max, y_max)
            boxes.append([scaled_min[0], scaled_min[1], scaled_max[0], scaled_max[1]])
            cv2.rectangle(canvas, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            cv2.imshow("image", canvas)
            print(f"BBox salva: {boxes[-1]}")

    cv2.namedWindow("image")
    cv2.setMouseCallback("image", on_mouse)
    cv2.imshow("image", canvas)
    print("Pressione 'q' para sair.")

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()

    return [{"bbox": bbox, "label": label} for bbox in boxes]


def annotate_report(
    report_dir: Path,
    variables: Sequence[str],
    *,
    input_func: Callable[[str], str] = input,
    sleep_func: Callable[[float], None] = time.sleep,
    annotation_func: Callable[[Path, str], List[BoxAnnotation]] = annotate_image,
) -> Dict[str, FieldAnnotation]:
    """Anota um relatório (pasta de páginas JPG) para um conjunto de variáveis."""

    pages = order_pages_by_index(report_dir.glob("*.jpg"))
    results: Dict[str, FieldAnnotation] = {}

    if not pages:
        print(f"Nenhuma página encontrada em {report_dir}")
        return results

    for variable in variables:
        total = len(pages)
        page_input = input_func(f"Escolha a página (1-{total}) para '{variable}': ")
        try:
            page_index = int(page_input) - 1
        except ValueError:
            print("Entrada inválida, variável ignorada.")
            continue

        if not 0 <= page_index < total:
            print("Página inválida, variável ignorada.")
            continue

        selected_page = pages[page_index]
        annotations = annotation_func(selected_page, variable)
        if annotations:
            results[variable] = {"bbox": annotations[0]["bbox"], "pagina": selected_page.name}
        else:
            print(f"Nenhum bounding box definido para '{variable}'.")

        sleep_func(2)

    return results


def annotate_companies(
    base_dir: Path,
    variables: Sequence[str],
    limits: Dict[str, int],
    *,
    annotation_func: Callable[[Path, str], List[BoxAnnotation]] = annotate_image,
    input_func: Callable[[str], str] = input,
    sleep_func: Callable[[float], None] = time.sleep,
) -> None:
    """Executa anotação para múltiplas empresas com limite de relatórios."""

    for company, limit in limits.items():
        company_dir = base_dir / company
        if not company_dir.exists():
            print(f"Diretório da empresa '{company}' não encontrado. Pulando.")
            continue

        reports = order_pages_by_index(p for p in company_dir.iterdir() if p.is_dir())

        for idx, report_dir in enumerate(reports[:limit], start=1):
            output_path = report_dir / f"{report_dir.name}.json"
            if output_path.exists():
                print(f"Arquivo existente para '{report_dir.name}', pulando.")
                continue

            print(f"[Empresa: {company}] Relatório {idx}/{limit}: {report_dir.name}")
            annotations = annotate_report(
                report_dir,
                variables,
                input_func=input_func,
                sleep_func=sleep_func,
                annotation_func=annotation_func,
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as handle:
                json.dump(annotations, handle, indent=4, ensure_ascii=False)

            print(f"Resultados salvos em: {output_path}")

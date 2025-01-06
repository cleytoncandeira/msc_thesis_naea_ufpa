import os
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from transformers import LayoutLMv2Processor, LayoutLMv2ForTokenClassification
import torch

# Caminho para o PDF experimental
pdf_path = "/home/cleyton/Documentos/ProjetosGit/meu_repositorio_dissertacao/data/external_data/audit_reports/audit_report_rtrs1.pdf"

# Inicializar o modelo LayoutLMv2-small
model_name = "microsoft/layoutlmv2-base-uncased"
processor = LayoutLMv2Processor.from_pretrained(model_name)
model = LayoutLMv2ForTokenClassification.from_pretrained(model_name)

# Função para converter PDF em imagens
def pdf_to_images(pdf_path):
    try:
        images = convert_from_path(pdf_path, dpi=100)
        return images
    except Exception as e:
        print(f"Erro ao converter PDF para imagens: {e}")
        return []

# Função para processar uma página com LayoutLMv2

def process_page_with_layoutlmv2(image):
    try:
        # Extrair texto e caixas de posição usando Tesseract
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        words = [ocr_data["text"][i] for i in range(len(ocr_data["text"])) if ocr_data["text"][i].strip() != ""]
        boxes = [
            [ocr_data["left"][i], ocr_data["top"][i], ocr_data["left"][i] + ocr_data["width"][i], ocr_data["top"][i] + ocr_data["height"][i]]
            for i in range(len(ocr_data["text"])) if ocr_data["text"][i].strip() != ""
        ]

        # Normalizar caixas para 0-1000
        width, height = image.size
        normalized_boxes = [[
            int(1000 * box[0] / width),
            int(1000 * box[1] / height),
            int(1000 * box[2] / width),
            int(1000 * box[3] / height)
        ] for box in boxes]

        # Tokenizar texto e caixas
        encoding = processor(
            words,
            boxes=normalized_boxes,
            return_tensors="pt",
            truncation=True,
            padding="max_length"
        )

        # Passar pelo modelo
        outputs = model(**encoding)
        logits = outputs.logits
        predictions = torch.argmax(logits, dim=2)

        # Decodificar previsões
        tokens = processor.tokenizer.convert_ids_to_tokens(encoding.input_ids[0])
        labels = predictions[0].tolist()

        return list(zip(tokens, labels))
    except Exception as e:
        print(f"Erro ao processar página com LayoutLMv2: {e}")
        return []

# Processar o PDF
try:
    print(f"Processing {pdf_path}")
    images = pdf_to_images(pdf_path)

    for page_num, image in enumerate(images):
        # Processar a página com LayoutLMv2
        results = process_page_with_layoutlmv2(image)

        # Procurar endereço nos resultados
        address_found = False
        for token, label in results:
            if "endereco" in token.lower():
                address_found = True
                print(f"Página {page_num + 1}: Token: {token}, Label: {label}")
        
        if not address_found:
            print(f"Página {page_num + 1}: Nenhuma informação relevante encontrada.")

except Exception as e:
    print(f"Erro ao processar o PDF: {e}")

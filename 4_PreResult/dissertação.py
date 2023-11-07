import torch
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import pipeline

# Carregue o modelo BERT pré-treinado para classificação de sentimento
model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertForSequenceClassification.from_pretrained(model_name)

# Crie uma função para avaliar o sentimento de uma frase
def avaliar_sentimento(frase):
    # Tokenize a frase
    inputs = tokenizer(frase, return_tensors="pt", truncation=True)

    # Faça a previsão de sentimento
    with torch.no_grad():
        outputs = model(**inputs)

    # Obtenha a classe de sentimento (0 a 4, onde 0 é muito negativo e 4 é muito positivo)
    sentiment_class = outputs.logits.argmax().item()

    # Mapeie a classe de sentimento para uma descrição
    sentiment_labels = ["Muito Negativo", "Negativo", "Neutro", "Positivo", "Muito Positivo"]
    sentiment = sentiment_labels[sentiment_class]

    return sentiment

# Frases de exemplo
frases = ["Eu amo esse filme, é incrível!", "Este produto é terrível e não funciona."]

# Avalie o sentimento das frases
for frase in frases:
    sentimento = avaliar_sentimento(frase)
    print(f'Frase: "{frase}" - Sentimento: {sentimento}')


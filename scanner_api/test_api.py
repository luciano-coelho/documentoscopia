import requests
import base64
import json
import os
import csv

TOKEN = "99be5c0890d6ac6f03aed3fed98631a8d6a53cd3"  # Substitua pelo seu token real

# Definir a pasta base onde estão as subpastas com os arquivos
base_folder = r"C:\Users\Luciano Figueiredo\Documents\Arquivos\Aprovadas"

# Verifica se a pasta base existe
if not os.path.exists(base_folder):
    print(f"Erro: Pasta base não encontrada {base_folder}")
    exit()

# Definir a URL da API
API_URL = "http://127.0.0.1:8000/api/documents/upload/"  # Ajuste conforme necessário

# Cabeçalhos com autenticação
headers = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}

# Função para determinar o tipo esperado de documento com base no nome do arquivo
def get_expected_document_type(file_name):
    file_name_lower = file_name.lower()
    if "cnh" in file_name_lower and "fisica" in file_name_lower:
        return "CNH Física"
    elif "cnh" in file_name_lower and "digital" in file_name_lower:
        return "CNH Digital"
    elif "rg" in file_name_lower and "frente" in file_name_lower:
        return "RG Frente"
    elif "rg" in file_name_lower and "verso" in file_name_lower:
        return "RG Verso"
    else:
        return "Documento Desconhecido"  # Tipo genérico para evitar falhas

# Lista para armazenar os resultados
results = []

# Percorrer todas as subpastas dentro da pasta base
for folder_name in os.listdir(base_folder):
    folder_path = os.path.join(base_folder, folder_name)

    # Verifica se é uma pasta
    if not os.path.isdir(folder_path):
        continue

    print(f"\nAnalisando arquivos na pasta: {folder_name}")

    # Obtém a lista de arquivos na pasta (qualquer tipo de imagem/PDF)
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf'))]

    # Se não houver arquivos, passa para a próxima pasta
    if not files:
        print(f"Aviso: Nenhum arquivo encontrado na pasta {folder_name}")
        continue

    # Percorre os arquivos encontrados na pasta
    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        print(f"Enviando arquivo: {file_name} (Origem: {folder_name})")

        # Define o tipo esperado do documento dinamicamente
        expected_document_type = get_expected_document_type(file_name)
        print(f"Tipo de Documento Identificado: {expected_document_type}")

        # Converte o arquivo para base64
        with open(file_path, "rb") as file:
            encoded_file = base64.b64encode(file.read()).decode("utf-8")

        # Criar o payload dinâmico
        payload = {
            "file_name": file_name,
            "file_contents_base64": encoded_file,
            "expected_document_type": expected_document_type
        }

        # Enviar a requisição para a API
        response = requests.post(API_URL, json=payload, headers=headers)
        response_json = response.json()

        # Corrigir erro ao acessar resposta como lista
        if isinstance(response_json, list) and response_json:
            response_data = response_json[0]  # Pegamos o primeiro elemento da lista
        else:
            response_data = {}

        status_code = response.status_code
        reason = response_data.get("reason", "N/A")
        score = response_data.get("score", 0)

        # Armazena o resultado na lista
        results.append([folder_name, file_name, expected_document_type, status_code, reason, score])

# Caminho do arquivo CSV
csv_file_path = os.path.join(os.getcwd(), "resultados.csv")

# Escrever os resultados no arquivo CSV
with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["folder_name", "file_name", "expected_document_type", "status_code", "reason", "score"])  # Cabeçalhos
    writer.writerows(results)  # Dados

print(f"\nProcessamento concluído. Resultados salvos em {csv_file_path}")

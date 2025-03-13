import os
import cv2
import numpy as np
import base64
import tempfile
import fitz  # PyMuPDF
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class DocumentUploadView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    parser_classes = (JSONParser,)


    def post(self, request, *args, **kwargs):
        # Captura os dados do payload
        file_name = request.data.get("file_name")
        file_contents_base64 = request.data.get("file_contents_base64")
        expected_document_type = request.data.get("expected_document_type", "").strip().lower()

        if not file_name or not file_contents_base64 or not expected_document_type:
            return Response(
                [{"error": "Campos obrigatórios ausentes"}],
                status=status.HTTP_400_BAD_REQUEST
            )

        # Decodifica o arquivo base64 e salva temporariamente
        try:
            file_data = base64.b64decode(file_contents_base64)
            temp_file_path = self.save_temp_file(file_data, file_name)
        except Exception as e:
            return Response(
                [{"error": f"Erro ao processar arquivo base64: {str(e)}"}],
                status=status.HTTP_400_BAD_REQUEST
            )

        # Valida o documento
        validation_result, score, looks_good = self.validate_document(file_name, temp_file_path, expected_document_type)

        # Remove o arquivo temporário após validação
        os.remove(temp_file_path)

        # Construir payload de resposta
        response_payload = [
            {
                "file_name": file_name,
                "looks_good": looks_good,
                "reason": validation_result,
                "score": score
            }
        ]

        print("\nPayload retornado:", response_payload)

        return Response(response_payload, status=status.HTTP_200_OK)

    def save_temp_file(self, file_data, file_name):
        """Salva temporariamente o arquivo recebido"""
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, file_name)
        with open(temp_file_path, "wb") as f:
            f.write(file_data)
        return temp_file_path

    def validate_document(self, file_name, file_path, expected_document_type):
        is_image = file_name.lower().endswith(('.jpg', '.jpeg', '.png'))
        is_pdf = file_name.lower().endswith('.pdf')

        # Tipos de documento esperados e suas regras
        valid_types = {
            "cnh física": is_image,
            "cnh digital": is_pdf,
            "rg frente": is_image,
            "rg verso": is_image,
        }

        if expected_document_type in valid_types and not valid_types[expected_document_type]:
            return f"Reprovada: {expected_document_type.capitalize()} deve ser um {'PDF' if is_pdf else 'arquivo de imagem'} ({file_name})", 0, False

        # Verificação de scanner e PB
        if is_image:
            image = cv2.imread(file_path)
            if image is None:
                return f"Erro: Não foi possível carregar a imagem ({file_name})", 100, False
            scanner_score = self.analyze_image(file_path)
            if scanner_score >= 55:
                return f"Reprovada: Documento escaneado ou fotocopiado ({file_name})", scanner_score, False
            if self.is_grayscale_image(image):
                return f"Reprovada: Imagem em Preto e Branco ({file_name})", 50, False

        return f"Aprovada: {file_name}", 0, True

    def analyze_image(self, file_path):
        """ Analisa se a imagem é escaneada ou uma foto. """
        image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            return 100  # Retorna pontuação alta para evitar erro

        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
        edges = cv2.Canny(image, 50, 150)
        edge_density = np.sum(edges > 0) / (image.shape[0] * image.shape[1])
        brightness_std = np.std(image)
        border_brightness = self.calcular_border_brightness(image)
        hist_variance = self.calcular_variacao_histograma(image)

        scanner_score = 0  

        # Refinamento das métricas para reduzir falso positivo
        if laplacian_var > 280:
            scanner_score += 20  
        if edge_density > 0.035:
            scanner_score += 25  
        if brightness_std < 27:
            scanner_score += 20  
        if border_brightness > 225:
            scanner_score += 10  
        if hist_variance < 600:
            scanner_score += 10  

        return scanner_score

    def is_grayscale_image(self, image, threshold=10):
        """ Verifica se a imagem é preto e branco """
        if len(image.shape) < 3:
            return True
        b, g, r = cv2.split(image)
        diff_rg = np.mean(np.abs(r - g))
        diff_rb = np.mean(np.abs(r - b))
        diff_gb = np.mean(np.abs(g - b))
        return diff_rg < threshold and diff_rb < threshold and diff_gb < threshold

    def calcular_border_brightness(self, image):
        """ Mede o brilho médio das bordas da imagem. """
        h, w = image.shape
        border_pixels = np.concatenate([image[0, :], image[-1, :], image[:, 0], image[:, -1]])
        return np.mean(border_pixels)

    def calcular_variacao_histograma(self, image):
        """ Calcula a variância do histograma da imagem. """
        hist = cv2.calcHist([image], [0], None, [256], [0, 256])
        return np.var(hist.flatten())

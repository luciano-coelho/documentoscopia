import cv2
import numpy as np

def analyze_image(file_path):
    """Analisa uma imagem e tenta identificar se foi escaneada ou fotografada."""
    
    image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return f"Erro: Não foi possível carregar a imagem. Caminho verificado: {file_path}"

    return analyze_image_from_array(image)

def analyze_image_from_array(image):
    """Analisa uma imagem já carregada em um array OpenCV."""
    
    if image is None or image.size == 0:
        return "Erro: Imagem inválida ou vazia"

    # 📌 1️⃣ Verifica a nitidez (usando Laplacian)
    laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()

    # 📌 2️⃣ Verifica bordas bem definidas (usando Canny)
    edges = cv2.Canny(image, 100, 200)
    edge_density = np.sum(edges) / (image.shape[0] * image.shape[1])

    # 📌 3️⃣ Verifica iluminação uniforme (desvio padrão do brilho)
    brightness_std = np.std(image)

    # 📌 4️⃣ Verifica presença de fundo
    border_crop = image[:10, :]  # Pega uma pequena faixa do topo
    border_brightness = np.mean(border_crop)

    # 📌 📊 Decisão baseada nos valores:
    if laplacian_var < 100 and brightness_std > 50:
        return "Provavelmente fotografado devido à baixa nitidez e iluminação irregular."
    elif edge_density > 0.02 and brightness_std < 30:
        return "Provavelmente escaneado devido à alta nitidez e iluminação uniforme."
    elif border_brightness < 220:  # Indica fundo diferente do branco
        return "Provavelmente fotografado porque há um fundo visível na imagem."
    else:
        return "Indeterminado. Pode ser uma foto bem iluminada de um documento escaneado."

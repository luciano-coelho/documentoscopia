import fitz  # PyMuPDF
import cv2
import numpy as np
from .image_processing import analyze_image_from_array

def analyze_pdf(file_path):
    """Extrai imagens do PDF e analisa cada uma delas."""
    
    doc = fitz.open(file_path)
    images_found = []

    for page_num in range(len(doc)):
        images = doc[page_num].get_images(full=True)
        
        if not images:
            images_found.append({f"Página {page_num + 1}": "Nenhuma imagem encontrada."})
            continue
        
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            
            if "image" not in base_image:
                images_found.append({f"Página {page_num + 1}, Imagem {img_index + 1}": "Erro: Imagem inválida."})
                continue
            
            img_bytes = base_image["image"]

            # Converte bytes para imagem OpenCV
            np_img = np.frombuffer(img_bytes, dtype=np.uint8)
            image = cv2.imdecode(np_img, cv2.IMREAD_GRAYSCALE)

            if image is None:
                images_found.append({f"Página {page_num + 1}, Imagem {img_index + 1}": "Erro: Não foi possível processar a imagem extraída."})
                continue

            # Realiza análise da imagem extraída
            result = analyze_image_from_array(image)
            images_found.append({f"Página {page_num + 1}, Imagem {img_index + 1}": result})

    return images_found if images_found else "Nenhuma imagem detectada no PDF."

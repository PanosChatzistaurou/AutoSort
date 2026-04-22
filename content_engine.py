import os
import sys
import pytesseract
from PIL import Image, ImageOps, ImageEnhance
import PyPDF2
import docx
from transformers import pipeline
import warnings

# I silence these because the transformers library is overly noisy and clutters the console
warnings.filterwarnings("ignore")

classifier = None

def init_nlp_model():
    global classifier
    if classifier is None:
        try:
            # I load this globally so I don't have to boot the heavy model for every single file
            classifier = pipeline(
                "zero-shot-classification", 
                model="./local_nlp_model" 
            )
        except Exception as e:
            print(f"Failed to load local model: {e}")

def get_tesseract_cmd():
    # packaging to an exe breaks standard paths, so i have to dynamically find where the ocr tool is hidden
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, 'Tesseract-OCR', 'tesseract.exe')

tesseract_cmd = get_tesseract_cmd()
if os.path.exists(tesseract_cmd):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
else:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path):
    try:
        # i force the image into sharp grayscale because the ocr engine struggles to read text on colorful or messy backgrounds
        img = Image.open(image_path).convert('L')
        img = ImageOps.autocontrast(img)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        return pytesseract.image_to_string(img).strip()
    except Exception:
        return ""

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            # we only scan the first three pages because reading an entire pdf takes way too long and the intro usually gives it away
            max_pages = min(len(reader.pages), 3)
            for i in range(max_pages):
                page_text = reader.pages[i].extract_text()
                if page_text: 
                    text += page_text + "\n"
    except Exception:
        pass
    return text.strip()

def extract_text_from_docx(docx_path):
    text = ""
    try:
        doc = docx.Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs if para.text])
    except Exception as e:
        print(f"Failed to extract DOCX: {e}")
    return text.strip()

def analyze_content_smart(text, user_tags, threshold=0.30):
    if not text or not user_tags or classifier is None: 
        return None
    
    # i cap the text length because feeding massive documents into the model takes forever and can freeze the app
    optimized_text = text[:1500] 

    try:
        result = classifier(optimized_text, candidate_labels=user_tags)
        best_match = result['labels'][0]
        confidence_score = result['scores'][0]
        
        if confidence_score > threshold:
            return best_match
        return None
            
    except Exception:
        return None
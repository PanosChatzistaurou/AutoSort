import os
import random
from pathlib import Path
from fpdf import FPDF
from PIL import Image, ImageDraw

# 1. Setup the Benchmark Directory
BASE_DIR = Path("Benchmark_Dataset")
BASE_DIR.mkdir(exist_ok=True)

# 2. Define our Test Data

EXTENSIONS = [
    # Images
    '.jpg', '.png', '.gif', '.bmp', '.svg', 
    # Documents
    '.docx', '.xlsx', '.pptx', '.rtf', 
    # Audio
    '.mp3', '.wav', '.flac', '.m4a',
    # Video
    '.mp4', '.mov', '.avi', '.mkv',
    # Executables & Archives
    '.exe', '.msi', '.zip', '.rar', '.7z',
    # Code
    '.py', '.js', '.html', '.css', '.json'
]
NLP_CATEGORIES = {
    # 1. Privacy-Critical (Proves the need for your local, air-gapped architecture)
    "Finance": ["invoice", "tax return", "receipt", "billing statement", "total amount due"],
    "Medical": ["patient diagnosis", "blood test results", "prescription", "clinical notes", "symptoms"],
    "Legal": ["contract", "lease agreement", "liability", "terms and conditions", "notary public"],
    
    # 2. Everyday Personal (Proves the tool works for the average user)
    "Academic": ["thesis draft", "lecture notes", "course syllabus", "bibliography", "research methodology"],
    "Career": ["resume", "cover letter", "work experience", "professional references", "interview schedule"],
    "Travel": ["flight itinerary", "boarding pass", "hotel reservation", "car rental", "booking confirmation"],
    
    # 3. Technical (Matches your specific extension filters)
    "Code": ["def calculate_sum():", "import sys", "class Main:", "console.log('error')", "while True:"]
}

def create_dummy_file(filename):
    """Creates a 1KB dummy file for basic extension testing."""
    filepath = BASE_DIR / filename
    with open(filepath, 'wb') as f:
        f.write(os.urandom(1024))

def create_pdf_with_text(filename, text_content):
    """Creates a real PDF with readable text for NLP testing."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text_content)
    pdf.output(str(BASE_DIR / filename))

def create_image_with_text(filename, text_content):
    """Creates a simple image with text for OCR testing."""
    img = Image.new('RGB', (400, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 50), text_content, fill=(0, 0, 0))
    img.save(BASE_DIR / filename)

print("Generating 100-File Benchmark Dataset...")

file_counter = 1

# --- GENERATE GROUP A: Control Group (40 files) ---
for _ in range(40):
    ext = random.choice(EXTENSIONS)
    create_dummy_file(f"standard_file_{file_counter}{ext}")
    file_counter += 1

# --- GENERATE GROUP B: Semantic Group (40 files) ---
for _ in range(20):
    # 20 PDFs
    category = random.choice(list(NLP_CATEGORIES.keys()))
    text = f"CONFIDENTIAL DOCUMENT\n\nCategory: {category}\n\nDetails: {random.choice(NLP_CATEGORIES[category])}"
    create_pdf_with_text(f"document_{file_counter}.pdf", text)
    file_counter += 1

for _ in range(20):
    # 20 Text files
    category = random.choice(list(NLP_CATEGORIES.keys()))
    text = f"Notes regarding {category}. Please review the {random.choice(NLP_CATEGORIES[category])}."
    with open(BASE_DIR / f"notes_{file_counter}.txt", 'w') as f:
        f.write(text)
    file_counter += 1

# --- GENERATE GROUP C: Trick Group (20 files) ---
for _ in range(10):
    # PDFs disguised as images
    category = random.choice(list(NLP_CATEGORIES.keys()))
    text = f"This file looks like a scan, but it is a {category} document containing: {random.choice(NLP_CATEGORIES[category])}"
    create_pdf_with_text(f"SCAN_IMG_{random.randint(1000,9999)}.pdf", text)
    file_counter += 1

for _ in range(10):
    # Images with OCR text but weird names
    category = random.choice(list(NLP_CATEGORIES.keys()))
    text = random.choice(NLP_CATEGORIES[category])
    create_image_with_text(f"whatsapp_download_{random.randint(100,999)}.png", f"URGENT {category.upper()}: {text}")
    file_counter += 1

print(f"Success! Created {file_counter - 1} files in '{BASE_DIR.absolute()}'")
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

# Windows users only (ignore if Mac/Linux)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text(file_path):

    # Check file type
    if file_path.endswith(".pdf"):
        return extract_from_pdf(file_path)
    else:
        return extract_from_image(file_path)


def extract_from_image(path):
    image = Image.open(path)
    text = pytesseract.image_to_string(image)
    return text


def extract_from_pdf(path):
    images = convert_from_path(
    path,
    poppler_path=r"D:\Downloads\poppler-25.12.0\Library\bin"
)

    full_text = ""

    for img in images:
        text = pytesseract.image_to_string(img)
        full_text += text + "\n"

    return full_text
import os
import base64
from groq import Groq
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image
import io

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def image_to_base64(image: Image.Image, fmt="JPEG") -> str:
    """Convert a PIL image to a base64-encoded string."""
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def extract_text_from_image_via_vision(image: Image.Image) -> str:
    """Use Groq Vision model to accurately extract all text from a medical report image."""
    b64 = image_to_base64(image)
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": (
                            "You are a precise medical data extraction AI. "
                            "Extract ALL text from this medical report image exactly as it appears. "
                            "Pay special attention to:\n"
                            "- ALL numerical values (preserve decimals exactly, e.g., 16.3, 3.22, 47.90)\n"
                            "- Test names, units, and reference ranges\n"
                            "- Patient information and lab details\n"
                            "Output the data in a structured table format: "
                            "Test Name | Result | Unit | Reference Interval\n"
                            "Do NOT interpret or add any commentary. Just extract the raw data faithfully."
                        )
                    }
                ]
            }
        ],
        temperature=0,
        max_tokens=2000
    )
    return response.choices[0].message.content.strip()


def extract_text(file_path: str) -> str:
    """
    Main entry point. Extracts text from an image or PDF using the Groq Vision model.
    Falls back gracefully on error.
    """
    try:
        if file_path.lower().endswith(".pdf"):
            return _extract_from_pdf(file_path)
        else:
            return _extract_from_image(file_path)
    except Exception as e:
        print(f"[OCR ERROR] Vision extraction failed: {e}")
        return ""


def _extract_from_image(path: str) -> str:
    image = Image.open(path).convert("RGB")
    print(f"[OCR] Using Groq Vision model for image: {path}")
    return extract_text_from_image_via_vision(image)


def _extract_from_pdf(path: str) -> str:
    pop_path = r"D:\Downloads\poppler-25.12.0\Library\bin" if os.name == "nt" else None
    images = convert_from_path(path, poppler_path=pop_path)

    full_text = ""
    for i, img in enumerate(images):
        print(f"[OCR] Processing PDF page {i + 1} with Groq Vision model...")
        full_text += extract_text_from_image_via_vision(img) + "\n\n"

    return full_text
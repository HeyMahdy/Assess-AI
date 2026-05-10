import base64
import io
import os
import boto3

import pypdf
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form, HTTPException


load_dotenv()



try:
    textract_client = boto3.client(
        'textract', 
        region_name='us-east-1',
        # Explicitly pulling the keys from your .env file
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
except Exception as e:
    print(f"Warning: Could not initialize AWS Textract. {e}")
    textract_client = None
app = FastAPI(title="AI Grading Engine API")


# ==========================================
# HELPER: STANDARD FILE PARSER
# ==========================================
async def parse_standard_file(contents: bytes, content_type: str) -> dict:
    """Helper function to parse PDFs or encode Images for the LLM."""
    if content_type.startswith("image/"):
        encoded_image = base64.b64encode(contents).decode("utf-8")
        image_data_url = f"data:{content_type};base64,{encoded_image}"
        return {"file_content": image_data_url, "file_type": "image"}
        
    elif content_type == "application/pdf":
        pdf_reader = pypdf.PdfReader(io.BytesIO(contents))
        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() + "\n"
            
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF. Might be a scanned image.")
        return {"file_content": extracted_text, "file_type": "pdf"}
    
    else:
         raise HTTPException(status_code=400, detail="Unsupported file type.")
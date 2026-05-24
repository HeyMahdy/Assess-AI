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
import base64
import pypdf
import io
from fastapi import HTTPException

async def parse_standard_file(contents_list: list[bytes], content_types_list: list[str]) -> dict:
    """
    Helper function to parse a batch of PDFs or encode images for the LLM.
    Returns a unified initial state payload for LangGraph.
    """
    # A list to store multiple image data URLs or text segments from all files
    processed_items = []
    
    # We use zip() to iterate through both lists side-by-side matching each file with its type
    for contents, content_type in zip(contents_list, content_types_list):
        
        if content_type.startswith("image/"):
            # Encode raw binary bytes into base64 text syntax
            encoded_image = base64.b64encode(contents).decode("utf-8")
            image_data_url = f"data:{content_type};base64,{encoded_image}"
            
            processed_items.append({"content": image_data_url, "type": "image"})
            
        elif content_type == "application/pdf":
            # Wrap bytes in a file-like stream object so pypdf can read it from memory
            pdf_reader = pypdf.PdfReader(io.BytesIO(contents))
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
                
            if not extracted_text.strip():
                raise HTTPException(status_code=400, detail="Could not extract text from PDF. Might be a scanned image.")
            
            processed_items.append({"content": extracted_text, "type": "pdf"})
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")
            
    # Return a single structure holding all parsed items
    return {"files": processed_items, "file_type": "batch_mix"}
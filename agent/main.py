import base64
import io
import traceback

import pypdf
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from api.service.Textract_service import parse_standard_file , textract_client
from config.db import get_db_connection
from utils.answer_agent.graph import build_graph as build_answer_graph
from utils.question_agent.graph import build_graph as build_question_graph
from utils.reviewer_agent.graph import build_graph as grading_app
from pydantic import BaseModel, Field
app_graph = build_answer_graph()
app_graph_01 = build_question_graph()
app_graph_02=grading_app()

load_dotenv()



# ==========================================
# 2. DEFINE THE FASTAPI ENDPOINT
# ==========================================

app = FastAPI(title="LangGraph PDF & Image Analyzer")

@app.get("/api/seed-data")
async def get_seed_data():
    teacher_id = "22222222-2222-2222-2222-222222222222"
    student_id = "STU-999"
    assignment_id = 99

    sql_questions = """
        SELECT question_label, question_description
        FROM public.questions
        WHERE teacher_id = %s AND assignment_id = %s
        ORDER BY question_label;
    """

    sql_answers = """
        SELECT question_label, answer
        FROM public.student_answers
        WHERE teacher_id = %s AND student_id = %s AND assignment_id = %s
        ORDER BY question_label;
    """

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_questions, (teacher_id, assignment_id))
                questions = cur.fetchall()
                cur.execute(sql_answers, (teacher_id, student_id, assignment_id))
                answers = cur.fetchall()

        return {
            "teacher_id": teacher_id,
            "student_id": student_id,
            "assignment_id": assignment_id,
            "questions": questions,
            "student_answers": answers,
        }
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{e.__class__.__name__}: {e}")


@app.get("/api/questions")
async def get_questions():
    teacher_id = "22222222-2222-2222-2222-222222222222"
    assignment_id = 99

    sql_questions = """
        SELECT question_label, question_description
        FROM public.questions
        WHERE teacher_id = %s AND assignment_id = %s
        ORDER BY question_label;
    """

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_questions, (teacher_id, assignment_id))
                questions = cur.fetchall()

        return {
            "teacher_id": teacher_id,
            "assignment_id": assignment_id,
            "questions": questions,
        }
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{e.__class__.__name__}: {e}")


@app.get("/api/rubrics")
async def get_rubrics():
    teacher_id = "22222222-2222-2222-2222-222222222222"
    assignment_id = 99

    sql_rubrics = """
        SELECT question_label, rubric_description
        FROM public.rubrics
        WHERE teacher_id = %s AND assignment_id = %s
        ORDER BY question_label;
    """

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_rubrics, (teacher_id, assignment_id))
                rubrics = cur.fetchall()

        return {
            "teacher_id": teacher_id,
            "assignment_id": assignment_id,
            "rubrics": rubrics,
        }
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{e.__class__.__name__}: {e}")

@app.post("/answer")
async def analyze_file_endpoint(
    file: UploadFile = File(...),
    teacher_id: str = Form(...),
    student_id: str = Form(...),
    assignment_id: int = Form(...),
):
    """
    Endpoint that accepts a PDF or an Image, processes it, 
    runs it through LangGraph, and returns the LLM's analysis.
    """
    # Read the file bytes into memory
    contents = await file.read()
    content_type = file.content_type

    try:
        # --- HANDLE IMAGES ---
        if content_type.startswith("image/"):
            # Encode image to base64 so GPT-4o can read it
            encoded_image = base64.b64encode(contents).decode("utf-8")
            image_data_url = f"data:{content_type};base64,{encoded_image}"
            
            initial_state = {
                "file_content": image_data_url,
                "file_type": "image",
                "teacher_id": teacher_id,
                "student_id": student_id,
                "assignment_id": assignment_id,
            }

        # --- HANDLE PDFs ---
        elif content_type == "application/pdf":
            # Extract text from the PDF
            pdf_reader = pypdf.PdfReader(io.BytesIO(contents))
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
                
            if not extracted_text.strip():
                raise HTTPException(status_code=400, detail="Could not extract text from the PDF. It might be a scanned image without OCR.")

            initial_state = {
                "file_content": extracted_text,
                "file_type": "pdf",
                "teacher_id": teacher_id,
                "student_id": student_id,
                "assignment_id": assignment_id,
            }

        # --- REJECT UNSUPPORTED FILES ---
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF or an Image.")

        # Execute the LangGraph workflow
        result = app_graph.invoke(initial_state)

        # Return the output to the user
        analysis = result.get("final_output")
        if analysis is None:
            analysis = result.get("extracted_data", result)

        return {
            "filename": file.filename,
            "type": initial_state["file_type"],
            "analysis": analysis,
        }

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{e.__class__.__name__}: {e}")
    




# ==========================================
# ENDPOINT 1: THE ANSWER EXTRACTOR
# ==========================================
@app.post("/question")
async def process_answer_endpoint(
    file: UploadFile = File(...),
    is_handwritten: bool = Form(...),
    is_rubric: bool = Form(...),
    teacher_id: str = Form(...),
    assignment_id: int = Form(...),
):
    """
    Processes a student's uploaded answer sheet.
    Uses LLM Vision for handwritten exams, and direct AWS Textract bytes for typed text.
    """
    contents = await file.read()
    
    try:
        if is_handwritten:
            # --- USE NORMAL LLM EXTRACTION FOR HANDWRITING ---
            initial_state = await parse_standard_file(contents, file.content_type)
            initial_state["document_type"] = "rubric" if is_rubric else "teacher_solve"
            initial_state["teacher_id"] = teacher_id
            initial_state["assignment_id"] = assignment_id
            result = app_graph_01.invoke(initial_state)
            
            return {
                "method_used": "llm_vision",
                "filename": file.filename,
                "analysis": result["final_output"]
            }

        else:
            # --- USE AWS TEXTRACT (DIRECT BYTES) FOR TYPED/NON-HANDWRITTEN ---
            if not textract_client:
                raise HTTPException(status_code=500, detail="AWS Textract client not configured.")
            
            # Send bytes directly to AWS Textract (No S3 required)
            response = textract_client.detect_document_text(Document={'Bytes': contents})
            
            # Stitch the detected lines together
            extracted_text = "\n".join(
                [item["Text"] for item in response.get("Blocks", []) if item.get("BlockType") == "LINE"]
            )
            
            if not extracted_text.strip():
                raise HTTPException(status_code=400, detail="Textract could not read the document.")
            
            # Pass the Textract output to your LangGraph to structure it into JSON
            initial_state = {"file_content": extracted_text, "file_type": "text"}
            initial_state["document_type"] = "rubric" if is_rubric else "teacher_solve"
            initial_state["teacher_id"] = teacher_id
            initial_state["assignment_id"] = assignment_id
            result = app_graph_01.invoke(initial_state)
            
            return {
                "method_used": "aws_textract_direct",
                "filename": file.filename,
                "analysis": result["final_output"]
            }

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{e.__class__.__name__}: {e}")







class GradeRequest(BaseModel):
    teacher_id: str
    student_id: str
    assignment_id: int

@app.post("/api/grade")
async def trigger_grading(request: GradeRequest):
    try:
        # Initial state to kick off the graph
        initial_state = {
            "teacher_id": request.teacher_id,
            "student_id": request.student_id,
            "assignment_id": request.assignment_id,
            "all_results": [] # Initialize empty array
        }
        
        # Invoke the graph synchronously (wait for all loops to finish)
        final_state = app_graph_02.invoke(initial_state)
        
        # Return only the aggregated results as JSON
        return {
            "status": "success",
            "student_id": request.student_id,
            "assignment_id": request.assignment_id,
            "results": final_state.get("all_results", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
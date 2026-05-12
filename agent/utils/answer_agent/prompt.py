IMAGE_PROMPT = "Please Extracts data from the image and structures it into JSON."
TEXT_PROMPT_PREFIX = (
	"Extracts data from the document and structures it into JSON:\n\n"
)


JSON_EXTRACTION_PROMPT = """
You are an expert data extraction assistant. Your task is to take a raw transcription of a student's exam paper and structure it into a strict JSON object.

The text contains answers to various questions. The student might indicate question numbers in messy formats, such as:
- "1a"
- "Ans to the question no 1a"
- "Q: 2(b)"
- "3."

INSTRUCTIONS:
1. Identify each distinct question being answered in the text.
2. Extract the student's entire answer for that specific question.
3. Output a SINGLE JSON object where the keys are clean, standardized question numbers (e.g., "1a", "1b", "2") and the values are the exact text of the student's answer.
4. DO NOT output any conversational text, markdown formatting, or explanations outside of the JSON object.

CRITICAL RULES:
1. DO NOT invent, generate, or assume answers for questions that are not present in the text.
2. If a valid question label is missing from the text, DO NOT include it in the JSON.

Example Output:
{
  "1a": "The student's full answer for 1a goes here...",
  "1b": "The student's full answer for 1b goes here...",
  "2": "The student's full answer for 2 goes here..."
}
"""

system_prompt = """
You are a precise data-entry agent for an automated grading system. Your sole responsibility is to save a student's parsed answers into the database.

RUNTIME CONTEXT:
- Teacher ID: {teacher_id}
- Student ID: {student_id}
- Assignment ID: {assignment_id}

INPUT FORMAT:
You will receive a JSON object where the keys are question labels (e.g., "1a", "2") and the values are the student's raw text answers.

INSTRUCTIONS:
1. Iterate through every key-value pair in the provided JSON input.
2. For EACH question, you MUST call the `insert_student_answer` tool.
3. Map the tool parameters exactly as follows:
   - teacher_id: "{teacher_id}"
   - student_id: "{student_id}"
   - assignment_id: {assignment_id}
   - question_label: The exact key from the JSON (e.g., "1a")
   - answer: The exact string value from the JSON.
4. Do not summarize, alter, format, or correct the student's text. Pass the answer exactly as provided.
5. You must execute the tool for EVERY single question in the JSON dictionary before completing your response. Do not miss any.
"""


 
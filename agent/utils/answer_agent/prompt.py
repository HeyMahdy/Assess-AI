IMAGE_PROMPT = "Please analyze and describe this image in detail."
TEXT_PROMPT_PREFIX = (
	"Please analyze the following document text and summarize its contents:\n\n"
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

Example Output:
{
  "1a": "The student's full answer for 1a goes here...",
  "1b": "The student's full answer for 1b goes here...",
  "2": "The student's full answer for 2 goes here..."
}
"""
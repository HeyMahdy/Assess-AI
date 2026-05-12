from typing import TypedDict


class AgentState(TypedDict):
	file_content: str
	file_type: str
	final_output: str
	teacher_id: str
	student_id: str
	assignment_id: int

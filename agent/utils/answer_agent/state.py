from typing import TypedDict


class AgentState(TypedDict):
	file_content: str
	file_type: str
	final_output: str

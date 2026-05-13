import json
from .tools import get_assignment_labels, fetch_evaluation_context
from .state import AssignmentState
from .prompt import grader_1_prompt,grader_2_prompt
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from .tools import tools
from langgraph.prebuilt import ToolNode

class GraderOutput(BaseModel):
    score: float = Field(
        description="The numeric score awarded based strictly on the rubric criteria."
    )
 
llm_strict = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
structured_llm_strict = llm_strict.with_structured_output(GraderOutput)

llm_strict_02 = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
structured_llm_strict_02 = llm_strict.with_structured_output(GraderOutput)


def init_supervisor_node(state: AssignmentState):
    """Fetches ALL labels for the assignment and creates the queue."""
    print("Supervisor: Initializing assignment queue...")
    
    print("this is the state")
    print(AssignmentState)
    result_str = get_assignment_labels.invoke({
        "teacher_id": state["teacher_id"],
        "assignment_id": state["assignment_id"]
    })

    print("this is the label data")
    print(result_str)
    
    data = json.loads(result_str)
    labels = data.get("labels", [])
    
    # Load the queue into the state
    return {"pending_labels": labels}

def fetch_next_context_node(state: AssignmentState):
    """Pops the next label from the queue and fetches its context."""
    # Get the current list of pending labels
    queue = state.get("pending_labels", [])
    
    # Pop the first label off the list
    next_label = queue.pop(0) 
    print(f"\nSupervisor: Setting up context for Question {next_label}...")
    
    # Fetch the context for THIS specific label
    result_str = fetch_evaluation_context.invoke({
        "teacher_id": state['teacher_id'],
        "student_id": state['student_id'],
        "assignment_id": state['assignment_id'],
        "question_label": next_label
    })
    data = json.loads(result_str)
    
    # Update the state with the new context AND the shortened queue
    return {
        "pending_labels": queue, # The list is now 1 item shorter!
        "current_label": next_label,
        "student_answer_id": data["student_answer_id"],
        "question_description": data["question_description"],
        "rubric_description": json.dumps(data["rubric_description"]),
        "student_answer": data["student_answer"]
    }



def grader_1_node(state: AssignmentState):
    """Executes the strict grading evaluation."""
    print(f"  -> Grader 1 evaluating {state['question_label']}...")
    
    # Format the prompt with the state variables
    messages = grader_1_prompt.format_messages(
        question_description=state["question_description"],
        rubric_description=state["rubric_description"],
        student_answer=state["student_answer"]
    )
    
    # Invoke the LLM (it automatically returns a Pydantic object)
    result = structured_llm_strict.invoke(messages)
    
    # Return the result as a dictionary to update the state
    return {
        "grader_1_result": {
            "score": result.score,
        }
    }

def grader_2_node(state: AssignmentState):
    """Executes the lenient/creative grading evaluation."""
    print(f"  -> Grader 2 evaluating {state['question_label']}...")
    
    messages = grader_2_prompt.format_messages(
        question_description=state["question_description"],
        rubric_description=state["rubric_description"],
        student_answer=state["student_answer"]
    )
    
    result = structured_llm_strict_02.invoke(messages)
    
    return {
        "grader_2_result": {
            "score": result.score,
            "label": AssignmentState["label"]
           
        }
    }


def aggregate_results_node(state: AssignmentState):
    """NEW: Catches parallel outputs, logs them, and appends to the final list."""
    print(f"  -> [Aggregator] Saving scores for {state['current_label']}...")
    
    combined_result = {
        "label": state["current_label"],
        "grader_1_score": state["grader_1_result"]["score"],
        "grader_2_score": state["grader_2_result"]["score"]
    }
    
    # operator.add handles appending this dict to the all_results list
    return {"all_results": [combined_result]}

# --- 4. ROUTING LOGIC ---

def supervisor_router(state: AssignmentState):
    """Checks if there are more questions in the queue."""
    if len(state.get("pending_labels", [])) > 0:
        return "fetch_next"
    else:
        print("\n[Supervisor] Queue empty. Grading complete!")
        return "END"
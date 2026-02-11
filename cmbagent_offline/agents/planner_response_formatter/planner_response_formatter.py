import os
from cmbagent.base_agent import BaseAgent
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any
import json
from pathlib import Path


class Subtasks(BaseModel):
    sub_task: str = Field(..., description="The sub-task to be performed")
    sub_task_agent: Literal["engineer", "researcher", "idea_maker", "idea_hater", "classy_sz_agent", "camb_agent", "classy_context", "camb_context"] =  Field(..., description="The name of the agent in charge of the sub-task")
    bullet_points: List[str] = Field(
        ..., description="A list of bullet points explaining what the sub-task should do"
    )

class PlannerResponse(BaseModel):
    # main_task: str = Field(..., description="The exact main task to solve.")
    sub_tasks: List[Subtasks]

    def format(self) -> str:
        plan_output = ""
        for i, step in enumerate(self.sub_tasks):
            plan_output += f"\n- Step {i + 1}:\n\t* sub-task: {step.sub_task}\n\t* agent in charge: {step.sub_task_agent}\n"
            if step.bullet_points:
                plan_output += "\n\t* instructions:\n"
                for bullet in step.bullet_points:
                    plan_output += f"\t\t- {bullet}\n"
        message = f"""
**PLAN**
{plan_output}
        """
        return message
        

class PlannerResponseFormatterAgent(BaseAgent):
    
    def __init__(self, llm_config=None, **kwargs):

        agent_id = os.path.splitext(os.path.abspath(__file__))[0]

        llm_config['config_list'][0]['response_format'] = PlannerResponse

        super().__init__(llm_config=llm_config, agent_id=agent_id, **kwargs)


    def set_agent(self,**kwargs):

        super().set_assistant_agent(**kwargs)








def _parse_plan_string(plan_str: str) -> List[Dict[str, Any]]:
    """
    Convert the markdown‐style plan string produced by PlannerResponse.format()
    back into a list[dict] matching the Subtasks model.
    """
    lines = [ln.rstrip() for ln in plan_str.splitlines()]
    subtasks: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
    in_instr = False

    for ln in lines:
        ln_stripped = ln.lstrip()

        # --- step header ----------------------------------------------------
        if ln_stripped.startswith("- Step"):
            if current:
                subtasks.append(current)
            current = {"bullet_points": []}
            in_instr = False
            continue

        # --- sub‑task -------------------------------------------------------
        if ln_stripped.startswith("* sub-task:"):
            if current is None:    # defensive
                current = {"bullet_points": []}
            current["sub_task"] = ln_stripped.removeprefix("* sub-task:").strip()
            continue

        # --- agent in charge -----------------------------------------------
        if ln_stripped.startswith("* agent in charge:"):
            current["sub_task_agent"] = (
                ln_stripped.removeprefix("* agent in charge:").strip()
            )
            continue

        # --- instructions block start --------------------------------------
        if ln_stripped.startswith("* instructions:"):
            in_instr = True
            continue

        # --- bullet points --------------------------------------------------
        if in_instr and ln_stripped.startswith("-"):
            current["bullet_points"].append(ln_stripped.removeprefix("-").strip())

    # add last task if any
    if current:
        subtasks.append(current)

    return subtasks


def save_final_plan(final_context: Dict[str, Any], work_dir: str) -> Path:
    """
    Save `final_context["final_plan"]` as structured JSON at
    <work_dir>/planning/final_plan.json.

    The JSON structure complies with:
        {
            "sub_tasks": [
                {
                    "sub_task": "...",
                    "sub_task_agent": "...",
                    "bullet_points": [...]
                },
                ...
            ]
        }
    """
    planning_dir = work_dir


    if "final_plan" not in final_context:
        raise KeyError('"final_plan" key missing from final_context')

    plan_obj = final_context.get("final_plan")

    # ---- Case 0: None - try to extract from alternative context keys ------
    if plan_obj is None:
        print("WARNING: final_plan is None, checking alternatives...")
        
        # Debug: show what we have
        print(f"plans = {final_context.get('plans')}")
        print(f"proposed_plan = {final_context.get('proposed_plan')}")
        print(f"reviews (first 500 chars) = {str(final_context.get('reviews'))[:500]}")
        print(f"recommendations (first 500 chars) = {str(final_context.get('recommendations'))[:500]}")
        
        # Try proposed_plan first, then plans (list of iterations)
        if final_context.get("proposed_plan"):
            plan_obj = final_context["proposed_plan"]
            print(f"Using 'proposed_plan': {type(plan_obj)}")
        elif final_context.get("plans") and len(final_context["plans"]) > 0:
            plan_obj = final_context["plans"][-1]
            print(f"Using last item from 'plans': {type(plan_obj)}")
        elif final_context.get("reviews") and len(final_context["reviews"]) > 0:
            # Maybe the plan is embedded in reviews?
            print(f"Checking reviews for plan data...")
            last_review = final_context["reviews"][-1]
            print(f"Last review type: {type(last_review)}, value: {str(last_review)[:500]}")
            # If it's a string containing plan format, use it
            if isinstance(last_review, str) and "Step" in last_review:
                plan_obj = last_review
                print("Using last review as plan")
        
        if plan_obj is None:
            # Last resort: check if there's a file with the plan already saved
            import glob
            work_dir = final_context.get("work_dir", "")
            print(f"work_dir = {work_dir}")
            if work_dir:
                plan_files = glob.glob(f"{work_dir}/**/*plan*.json", recursive=True)
                print(f"Found plan files: {plan_files}")
            
            raise ValueError("final_plan is None and no alternative found")

    # ---- Case 1: a Pydantic object ----------------------------------------'''
    if hasattr(plan_obj, "model_dump"):          # Pydantic v2
        plan_dict = plan_obj.model_dump()
    elif hasattr(plan_obj, "dict"):              # Pydantic v1
        plan_dict = plan_obj.dict()

    # ---- Case 2: already a dict / list ------------------------------------
    elif isinstance(plan_obj, (dict, list)):
        plan_dict = {"sub_tasks": plan_obj} if isinstance(plan_obj, list) else plan_obj

    # ---- Case 3: formatted string -----------------------------------------
    elif isinstance(plan_obj, str):
        plan_dict = {"sub_tasks": _parse_plan_string(plan_obj)}
    else:
        print(f"DEBUG: final_plan type = {type(plan_obj)}")
        print(f"DEBUG: final_plan value = {plan_obj}")
        print(f"DEBUG: final_context keys = {final_context.keys()}")
        raise TypeError(
            f'"final_plan" must be a PlannerResponse, dict/list, or formatted string. Got {type(plan_obj)}: {plan_obj}'
        )

    # ---- Write the JSON ----------------------------------------------------
    json_path = planning_dir / "final_plan.json"
    with json_path.open("w", encoding="utf-8") as fp:
        json.dump(plan_dict, fp, ensure_ascii=False, indent=4)

    return json_path


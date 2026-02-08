"""Functions for execution flow control and transitions."""

from typing import Literal, Optional
from autogen.agentchat.group import ContextVariables
from autogen.agentchat.group import AgentTarget, ReplyResult, TerminateTarget


def create_post_execution_transfer(controller, engineer, camb_context, installer, terminator):
    """Factory function to create post_execution_transfer with agent references."""

    def post_execution_transfer(
        next_agent_suggestion: Literal["engineer", "installer", "camb_context", "controller"],
        context_variables: ContextVariables,
        execution_status: Literal["success", "failure"],
        fix_suggestion: Optional[str] = None
    ) -> ReplyResult:
        """Transfer to the next agent based on execution status.

        Note: execution_status is the CODE execution status (did the code run without errors).
        This is different from step_execution_status (is the plan step goal achieved).
        Only the controller should mark a step as complete.
        """
        # Store code execution status in context for controller to see
        context_variables["code_execution_status"] = execution_status

        workflow_status_str = rf"""
xxxxxxxxxxxxxxxxxxxxxxxxxx

Workflow status:

Plan step number: {context_variables["current_plan_step_number"]}

Agent for sub-task (might be different from the next agent suggestion for debugging): {context_variables["agent_for_sub_task"]}

Current status (before execution): {context_variables["current_status"]}

Code execution status: {execution_status}

Step execution status: {context_variables.get("step_execution_status", "in_progress")}

xxxxxxxxxxxxxxxxxxxxxxxxxx
"""

        if context_variables["agent_for_sub_task"] == "engineer" or \
           context_variables["agent_for_sub_task"] == "camb_context":

            if context_variables["n_attempts"] >= context_variables["max_n_attempts"]:
                return ReplyResult(
                    target=AgentTarget(terminator),
                    message=f"Max number of code execution attempts ({context_variables['max_n_attempts']}) reached. Exiting.",
                    context_variables=context_variables
                )

            if execution_status == "success":
                # Code ran successfully - return to controller to decide if step is complete
                # Note: This does NOT mean the step is complete, just that code executed without errors
                return ReplyResult(
                    target=AgentTarget(controller),
                    message="Code execution status: " + execution_status + ". Transfer to controller to evaluate step progress.\n" + f"{workflow_status_str}\n",
                    context_variables=context_variables
                )

            if next_agent_suggestion == "engineer":
                context_variables["n_attempts"] += 1
                return ReplyResult(
                    target=AgentTarget(engineer),
                    message="Code execution status: " + execution_status + ". Transfer to engineer.\n" + f"{workflow_status_str}\n" + f"Fix suggestion: {fix_suggestion}\n",
                    context_variables=context_variables
                )

            elif next_agent_suggestion == "camb_context":
                context_variables["n_attempts"] += 1
                return ReplyResult(
                    target=AgentTarget(camb_context),
                    message="Code execution status: " + execution_status + ". Transfer to camb_context.\n" + f"{workflow_status_str}\n" + f"Fix suggestion: {fix_suggestion}\n",
                    context_variables=context_variables
                )

            elif next_agent_suggestion == "controller":
                context_variables["n_attempts"] += 1
                return ReplyResult(
                    target=AgentTarget(controller),
                    message="Code execution status: " + execution_status + ". Transfer to controller.\n" + f"{workflow_status_str}\n",
                    context_variables=context_variables
                )

            elif next_agent_suggestion == "installer":
                context_variables["n_attempts"] += 1
                return ReplyResult(
                    target=AgentTarget(installer),
                    message="Code execution status: " + execution_status + ". Transfer to installer.\n" + f"{workflow_status_str}\n",
                    context_variables=context_variables
                )
        else:
            return ReplyResult(
                target=AgentTarget(controller),
                message="Transfer to controller.\n" + workflow_status_str,
                context_variables=context_variables
            )

    return post_execution_transfer


def create_terminate_session():
    """Factory function to create terminate_session."""

    def terminate_session(context_variables: ContextVariables) -> ReplyResult:
        """Terminate the session."""
        return ReplyResult(
            target=TerminateTarget(),
            message="Session terminated.",
            context_variables=context_variables
        )

    return terminate_session

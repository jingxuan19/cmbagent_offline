from pathlib import Path
import cmbagent


def test_deep_research():

    task = r"""
    draw 100 random numbers from a normal distribution with mean 0 and standard deviation 1.
    plot the histogram of the numbers.
    """

    results = cmbagent.deep_research(
        task,
        max_rounds_control=100,
        n_plan_reviews=1,
        max_n_attempts=4,
        max_plan_steps=4,
        # engineer_model="gemini-3-flash-preview",
        # engineer_model="gemini-2.5-flash",
        planner_model="gpt-oss-120b",
        engineer_model="gpt-oss-120b",
        researcher_model="gpt-oss-120b",
        # default_llm_model="gpt-oss-120b",
        default_formatter_model="gpt-oss-120b",
        plan_reviewer_model="claude-sonnet-4-20250514",
        plan_instructions=r"""
Use researcher to do some reasoning and then use engineer for the whole analysis, and finally researcher to report the results. Plan must have 4 steps:
1. researcher
2. engineer
3. engineer
4. researcher
""",
        # work_dir=str(tmp_path / "deep_research"),
        work_dir="/Users/boris/Desktop/deep_research",
        clear_work_dir=True,
    )

    assert results is not None


test_deep_research()
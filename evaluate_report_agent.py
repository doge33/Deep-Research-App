from agents import Agent
from pydantic import BaseModel, Field

INSTRUCTIONS3 = """
    You are a helpful but strict assistant that judges the quality of a research report based on a research brief.
    Judging criteria:
    - the report addresses all the requested information, such as scope, timeframe, specific area/research angles/audience, key comparisons, etc..
    - the report is concise, clear, useful and easy to read.
    Provide a result and a brief reasoning or feedback for your judgement.
    """

class ReportEvaluation(BaseModel):
    is_acceptable: bool=Field(description="The judgment result of whether the report passed the evaluation")
    reasoning: str=Field(description="Reasoning for the judgement including improvement suggestions if evaluation has failed")

evaluate_report_agent = Agent(
    name="Evaluate Report Agent",
    instructions=INSTRUCTIONS3,
    model = "gpt-4o", #use a stronger model for evaluating stuff
    output_type=ReportEvaluation
)
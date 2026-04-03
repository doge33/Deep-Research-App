from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, clearly structured,and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."

    """Assume this HTML will be:
    1) displayed inside a Gradio app, and
    2) sent as an email body.

    Therefore:
    - Avoid internal anchor links entirely.
    - Avoid advanced CSS.
    - Prefer simple, robust HTML that degrades well in email clients.
    - If including a Table of Contents, make it non-clickable.
    - Make sure subheaders are always properly indented both inside the Table of Contents and the actual contents body of the report
    """
    
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")

    markdown_report: str = Field(description="The final report")

    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)
from agents import Agent
from pydantic import BaseModel, Field

INSTRUCTIONS = """
    You are a helpful research assistant. You are given the user's original query and maybe further clarification questions with the user's answers to them.
    Build a clean, structured brief that becomes the finalized research query.
"""
# DO I REALLY NEED A STRUCTURED OUTPUT FOR THIS OR IS STR OUTPUT ENOUGH?
class ResearchBrief(BaseModel):
    original_query: str = Field(description="The original query that the user entered in the beginning")
    clarified_query: str = Field(description="a more refined research query based on the user's answers to clarification questions")

brief_builder_agent = Agent(
    name = "Brief Builder Agent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ResearchBrief
)
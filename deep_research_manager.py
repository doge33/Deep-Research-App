from agents import Runner, trace, gen_trace_id
from need_clarifications_agent import need_clarifications_agent, ClarificationDecision
from brief_builder_agent import brief_builder_agent, ResearchBrief
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from evaluate_report_agent import evaluate_report_agent, ReportEvaluation
from email_agent import email_agent
import asyncio
from dotenv import load_dotenv

load_dotenv(override=True)

class DeepResearchManager:

    def __init__(self) -> None:
         self.pending_clarification = None

    async def run(self, query:str):
        """Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Deep Research Trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            # =============Intake Verification=====================
            final_brief = await self.refine_research_query(query)
            # brief was not built when clarification needed          
            if(final_brief) == None:
                further_questions = "\n".join(
                    f"\n{i+1}. {q}\n" for i, q in enumerate(self.pending_clarification["questions"]))                   
                yield f"Please answer the following questions in order to better prepare the deep research:\n{further_questions}"
                return
            # brief was built otherwise
            yield f"Researching: {final_brief}"
            print(f"Researching: {final_brief}")

            # ===========Plan and Execute Research===============
            print("Planning research...")
            search_plan = await self.plan_searches(query)

            yield "Searches planned, starting to search..."     
            search_results = await self.perform_searches(search_plan)

            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)

            # ===========Evaluate the report by another model=======
            yield "report generated, evaluating report..."
            evaluation = await self.evaluate_report(final_brief, report)
            yield f"This Report has passed evaluation: {evaluation.is_acceptable}\nReason:{evaluation.reasoning}"
            print(f"This Report has passed evaluation: {evaluation.is_acceptable}\nReason:{evaluation.reasoning}")

            #===========Email Report==============================
            yield "Sending email..."
            await self.send_email(report)

            yield "Email sent, research complete"
            yield report.markdown_report







    async def refine_research_query(self,query:str):
        """given a user query, check if clarification is needed, update the pending_clarification status and write a clean final research brief"""
        
        print(f"top of screen_research_query. pending_clarification = {self.pending_clarification}")
        # CASE 1. second run, when we are waiting for user input to clarification answers. the pending_clarification dict was populated before
        if self.pending_clarification:
            original_query = self.pending_clarification["original_query"]
            questions = self.pending_clarification["questions"]
            user_answers = query #this is the 2nd time query now
        
            # build research brief using all the input so far
            brief = await self.build_research_brief(original_query, questions, user_answers)

            self.pending_clarification = None # done with the work here, reset state
            print("Clarification questions answered. Brief constructed. Return brief")
            return brief
        

        
        decision = await self.clarify_query(query)
        # CASE2. normal first run, but need clarification; state is None at this point
        # update state:
        if decision.needs_clarifications:
            self.pending_clarification = {
                "original_query": query,
                "questions": decision.questions,
            }
            # yield f"Please answer the following questions in order to better prepare the deep research:\n{decision.questions}"
            print(f"Clarification needed, pending state saved. No brief returned.")
            return None

        # CASE3. otherwise - first time query and no need for clarify
        brief = await self.build_research_brief(query, [], "")
        print("First time query OK. Return brief.")
        return brief


    async def clarify_query(self, query:str) -> ClarificationDecision:
        """use the need_clarification_agent to check if further clarification is needed"""
        print("Checking if further clarification is needed...")
        result = await Runner.run(need_clarifications_agent, f"Query:{query}")
        return result.final_output

    async def build_research_brief(self, original_query:str, clarification_questions:list, user_answers:str="") -> str:
        input = f"Original query:\n{original_query} \n Clarification questions:\n{clarification_questions} \n User's answers: {user_answers}"
        result = await Runner.run(brief_builder_agent, input)
        return result.final_output.clarified_query

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        # creates and schedules the coroutines to run immediately in the background
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []

        #yields tasks one by one as soon as each finishes 
        # # (process rresultts in completion order, no original order)
        # different from asyncio.gather, which returns results in original task order!!
        for task in asyncio.as_completed(tasks): # process result of each task as soon as it completed
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed") #shows how many tasks out of all completed
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write the report for the query """
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def evaluate_report(self, brief:str, report:str) -> ReportEvaluation:
        """evaluate the report's quality"""
        print("Evaluating report")
        input = f"Research Brief:{brief}\n Report Generated:{report}"
        result = await Runner.run(evaluate_report_agent, input)
        print("Finish evaluation")
        return result.final_output_as(ReportEvaluation)

    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
        return report




# async def call():
#     new_manager = DeepResearchManager()
#     result = await new_manager.screen_research_query("today's market")
#     return result

# print(asyncio.run(call()))
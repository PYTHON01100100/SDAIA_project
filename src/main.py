import asyncio
#import os
import sys

from dotenv import load_dotenv

from src.agent.specialists import create_researcher, create_analyst, create_writer
from src.observability.tracer import tracer # TODO: Unleash the tracer
from src.observability.cost_tracker import CostTracker
import litellm
litellm.suppress_debug_info = True   # silence "Provider List" spam
litellm.drop_params = True           # drop unsupported params (e.g. tool_choice) silently
#litellm._turn_on_debug()

# Load environment variables
load_dotenv()


async def main():
    """
    Main entry point for the AI Agent system.
    """
    # 1. Get the query
    if len(sys.argv) < 2:
        print("Usage: python -m src.main \"Your research query\"")
        sys.exit(1)

    query = sys.argv[1]
    print(f"Starting research on: {query}")

    # TODO: Initialize your agents here
    # Use the Factory Pattern to create agents.
    # The 'create_researcher' function (and others) acts as a factory, encapsulating 
    # the creation logic (prompt selection, tool assignment) for each agent type.
    cost_tracker = None
    writing_result = None
    try:
        # Start global trace
        trace_id=tracer.start_trace(agent_name="MainAgent", query=query)

        cost_tracker = CostTracker()
        cost_tracker.start_query(query)

        researcher = create_researcher()
        analyst = create_analyst()
        writer = create_writer()

    # TODO: Create the orchestrator or main loop
    # In the final project, we might use an ArchitectureDecisionEngine here to decide
    # which agent architecture (Single vs Multi-Agent) to run. 
    # For this starter, you can implement a simple linear chain (Researcher -> Analyst -> Writer)
    # or a loop.
    # ...
        # Stage 1: Research
        research_result = await researcher.run(query)
        if "error" in research_result:
            print(f"Research failed: {research_result['error']}")
            return

        # Stage 2: Analysis
        analysis_query = f"Analyze these findings: {research_result['answer']}"
        analysis_result = await analyst.run(analysis_query)
        if "error" in analysis_result:
            print(f"Analysis failed: {analysis_result['error']}")
            return

        # Stage 3: Writing
        writing_query = f"Write a report based on: {analysis_result['answer']}"
        writing_result = await writer.run(writing_query)
        if "error" in writing_result:
            print(f"Writing failed: {writing_result['error']}")
            return

        # Final output
        print(writing_result["answer"])
        tracer.end_trace(
            trace_id=trace_id,
            output=writing_result["answer"] if writing_result else "",
            status="completed")
        cost_tracker.end_query()
        total_cost = (research_result.get("cost", 0.0) + 
                     analysis_result.get("cost", 0.0) + 
                     writing_result.get("cost", 0.0))
        print(f"\nTotal Cost: ${total_cost:.6f}")
    except Exception as e:
        if cost_tracker is not None:
            cost_tracker.end_query()
            output = writing_result["answer"] if writing_result else ""
            tracer.end_trace(trace_id=trace_id, output=output, status="failed")
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
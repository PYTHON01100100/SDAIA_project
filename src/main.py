from dotenv import load_dotenv
load_dotenv()

import sys
import asyncio
from agent.specialists import create_researcher, create_analyst, create_writer
from observability.cost_tracker import CostTracker

async def main():
    if len(sys.argv) < 2:
        print('Usage: python -m src.main "Your research query"')
        sys.exit(1)

    query = sys.argv[1]
    print(f"\n🔎 Starting research on: {query}\n")

    tracker = CostTracker()
    tracker.start_query(query)

    # Agents
    researcher = create_researcher()
    analyst = create_analyst()
    writer = create_writer()

    # Run Researcher
    print("Running Researcher...\n")
    research_result = await researcher.run(query)
    tracker.log_agent_usage(
        agent_name="Researcher",
        model=research_result["model_used"],
        input_tokens=research_result["total_input_tokens"],
        output_tokens=research_result["total_output_tokens"],
    )

    # Run Analyst
    print("\nRunning Analyst...\n")
    analysis_result = await analyst.run(research_result["answer"])
    tracker.log_agent_usage(
        agent_name="Analyst",
        model=analysis_result["model_used"],
        input_tokens=analysis_result["total_input_tokens"],
        output_tokens=analysis_result["total_output_tokens"],
    )

    # Run Writer
    print("\nRunning Writer...\n")
    final_result = await writer.run(analysis_result["answer"])
    tracker.log_agent_usage(
        agent_name="Writer",
        model=final_result["model_used"],
        input_tokens=final_result["total_input_tokens"],
        output_tokens=final_result["total_output_tokens"],
    )

    tracker.end_query()
    tracker.print_cost_breakdown()

    print("\n================ FINAL OUTPUT ================\n")
    print(final_result["answer"])
    print("\n==============================================\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "Event loop is closed" not in str(e):
            raise e

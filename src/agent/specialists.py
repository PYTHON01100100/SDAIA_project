from src.agent.observable_agent import ObservableAgent
from src.tools.registry import registry

def create_researcher(model: str = "openrouter/z-ai/glm-4.5-air:free", max_steps: int = 15):
    """
    The Researcher: finds, retrieves, and extracts information.
    
    This function implements the Factory Pattern, returning a configured ObservableAgent
    specialized for research tasks.
    """
    # TODO: Implement this factory
    # 1. Define system prompt (e.g. "You are a world-class researcher...")
    # 2. Get research tools from registry (e.g. registry.get_tools_by_category("research"))
    # 3. Create and return ObservableAgent with these tools and prompt
    RESEARCHER_PROMPT = """You are a Research Specialist. Your ONLY job is
    to find and retrieve relevant information. You do NOT analyze or write.

    Your standards:
    - Always cite your sources with URLs or document references.
    - If search results are thin, reformulate your query before giving up.
    - Return raw findings organized by source. Do NOT editorialize."""
    research_tools = registry.get_tools_by_category("research")
    return ObservableAgent(
        model=model,
        max_steps=max_steps,
        agent_name="Researcher",
        verbose=True,
        system_prompt=RESEARCHER_PROMPT,
        tools=research_tools
    )


def create_analyst(model: str = "openrouter/z-ai/glm-4.5-air:free", max_steps: int = 20):
    """
    The Analyst: evaluates, cross-references, and identifies patterns.
    """
    # TODO: Implement this factory
    ANALYST_PROMPT = """You are an Analysis Specialist. Your ONLY job is to evaluate information and extract insights.
    
    Your standards:
    - Cross-reference claims across sources. Flag contradictions explicitly.
    - Distinguish between facts, opinions, and speculation.
    - Identify gaps: what important questions does the research NOT answer?
    - Rate confidence: High / Medium / Low per claim."""

    # Get analysis tools from registry
    analysis_tools = registry.get_tools_by_category("analysis")
    
    return ObservableAgent(
        model=model,
        max_steps=max_steps,
        agent_name="Analyst",
        verbose=True,
        system_prompt=ANALYST_PROMPT,
        tools=analysis_tools
    )

def create_writer(model: str = "openrouter/z-ai/glm-4.5-air:free", max_steps: int = 4):
    """
    The Writer: synthesizes analysis into polished, readable output.
    """
    # TODO: Implement this factory
    WRITER_PROMPT= """You are a Writing Specialist. Your ONLY job is 
    to take analyzed research and produce a clear, well-structured document.
    Your standards:
    - Write for the specified audience (default: informed professional).
    - Structure with clear headings, topic sentences, and transitions.
    - Preserve source citations from the research phase.
    - Include confidence qualifiers from the analysis."""
    writing_tools = registry.get_tools_by_category("Writing")
    return ObservableAgent(
        model=model,
        max_steps=max_steps,
        agent_name="Writing",
        verbose=True,
        system_prompt=WRITER_PROMPT,
        tools=writing_tools
    )

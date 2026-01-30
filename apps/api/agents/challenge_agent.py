from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

async def generate_system_design_challenge(primitives: List[str]) -> str:
    if not primitives:
        return "No primitives available for a challenge."

    # Assuming OPENAI_API_KEY is in environment
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Senior Staff Engineer creating a System Design interview question."),
        ("user", """
        Create a 'System Design Challenge' that forces the candidate to use the following concepts (Decision Primitives):

        {primitives}

        The challenge should be:
        1. A realistic scenario (e.g., "Design a notification system for 10M users").
        2. Explicitly require using the listed primitives to solve specific constraints.
        3. Short and punchy (suitable for a Slack notification).
        """)
    ])

    chain = prompt | llm | StrOutputParser()

    try:
        result = await chain.ainvoke({"primitives": ", ".join(primitives)})
        return result
    except Exception as e:
        return f"Error generating challenge: {e}"

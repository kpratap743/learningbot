from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class RFCCritiqueResult(BaseModel):
    organizational_leverage: str = Field(description="Analysis of whether this solves a problem for one team or the whole org")
    alternative_analysis: str = Field(description="Analysis of 'Buy vs Build' consideration")
    operational_excellence: str = Field(description="Mentions of backpressure, circuit breakers, and observability")
    delta_report: str = Field(description="What is missing to reach Principal bar")

class RFCCritiqueAgent:
    def __init__(self):
        # Assuming OPENAI_API_KEY is in environment
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

    async def critique(self, content: str) -> RFCCritiqueResult:
        parser = JsonOutputParser(pydantic_object=RFCCritiqueResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a 'Staff Design Review Committee' member."),
            ("user", """
            Review the following RFC document acting as a 'Staff Design Review Committee'.

            Document Content:
            {content}

            Evaluate the document based on the following criteria:

            1. Organizational Leverage: Does this solve a problem for one team or the whole org?
            2. Alternative Analysis: Did the author consider 'Buy vs Build'?
            3. Operational Excellence: Are there mentions of backpressure, circuit breakers, and observability?

            Provide the output as a structured critique including a 'Delta Report' showing what is missing to reach the Principal bar.

            {format_instructions}
            """)
        ])

        chain = prompt | self.llm | parser

        try:
            result = await chain.ainvoke({
                "content": content,
                "format_instructions": parser.get_format_instructions()
            })
            return RFCCritiqueResult(**result)
        except Exception as e:
            print(f"Error in RFCCritiqueAgent: {e}")
            # Return a fallback or re-raise depending on desired behavior.
            # Here we return an error state.
            return RFCCritiqueResult(
                organizational_leverage="Error processing request",
                alternative_analysis="Error processing request",
                operational_excellence="Error processing request",
                delta_report=f"Error: {str(e)}"
            )

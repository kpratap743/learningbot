from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class StrategyCriticResult(BaseModel):
    spof: str = Field(description="Analysis of Single Point of Failure in the architecture")
    hidden_complexity: str = Field(description="Identification of Hidden Complexity or Tech Debt trade-offs")
    organizational_leverage: str = Field(description="Evaluation of Organizational Leverage and benefits to other teams")
    principal_gap_report: str = Field(description="Report highlighting where the document is too feature-focused rather than strategy-focused")

class StrategyCritic:
    def __init__(self):
        # Assuming OPENAI_API_KEY is in environment
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

    async def analyze(self, content: str) -> StrategyCriticResult:
        parser = JsonOutputParser(pydantic_object=StrategyCriticResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a 'Staff-level Critic' reviewing an RFC."),
            ("user", """
            Analyze the following RFC document acting as a 'Staff-level Critic'.

            Document Content:
            {content}

            Your instructions are:
            1. Look for 'Single Point of Failure' (SPOF) in the architecture.
            2. Identify 'Hidden Complexity' or 'Tech Debt' trade-offs.
            3. Evaluate 'Organizational Leverage' (How does this benefit other teams?).
            4. Output a 'Principal Gap Report' highlighting where the document is too feature-focused rather than strategy-focused.

            Provide the output as a structured analysis.

            {format_instructions}
            """)
        ])

        chain = prompt | self.llm | parser

        try:
            result = await chain.ainvoke({
                "content": content,
                "format_instructions": parser.get_format_instructions()
            })
            return StrategyCriticResult(**result)
        except Exception as e:
            # Fallback for error handling
            return StrategyCriticResult(
                spof="Error processing request",
                hidden_complexity="Error processing request",
                organizational_leverage="Error processing request",
                principal_gap_report=f"Error: {str(e)}"
            )

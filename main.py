import argparse
import os
from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.utils.pprint import pprint_run_response
from agno.run.agent import RunOutput


DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def get_language(text: str) -> str:
    model = DeepSeek(api_key=DEEPSEEK_API_KEY)
    agent = Agent(
        model=model,
        name="language-identifier",
        description="A tool to identify the language of the text.",
        session_state={"language": None},
        instructions="Understand the language of the text. Assign the session_state['language'] with the language of the text (one word).",
    )
    agent.run(f"Please identify the language of the following text:\n'{text}'")
    return agent.session_state["language"]

def check_text(text: str, language: str) -> str:
    """Verify text correctness and return the AI response as a string."""
    model = DeepSeek(id="deepseek-chat", api_key=DEEPSEEK_API_KEY)
    agent = Agent(
        model=model,
        name="text-checker",
        description="A tool to verify the correctness of written text.",
        session_state={"language": language},
        instructions="""
        Verify the correctness of the provided text in the session_state['language'] language. 
        Does this word / phrase / text makes sense? Is it grammatically correct? 
        If the usage is somewhat wrong -- propose a correction.
        If the grammar is wrong -- propose a correction.
        """,
    )
    
    # Run agent and return the response as a variable
    response: RunOutput = agent.run(f"Please verify the correctness of the following text:\n'{text}'")

    # Extract the response content as string
    if response.messages and len(response.messages) > 0:
        return response.messages[-1].content
    return "Unable to process the text."


def process_text(text: str) -> str:
    """Process text and return the AI response as a string.
    
    This is the main entry point for external callers (e.g., Telegram bot).
    """
    language = get_language(text)
    return check_text(text, language)

def main():
    """CLI entry point for text verification."""
    argparser = argparse.ArgumentParser()
    argparser.add_argument("text", type=str, help="The text to verify")
    args = argparser.parse_args()
    text = args.text
    result = process_text(text)
    print(result)

if __name__ == "__main__":
    main()

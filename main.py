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

def check_text(text: str, language: str) -> bool:
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

    # Print the response in markdown format
    pprint_run_response(response, markdown=True)

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("text", type=str, help="The text to verify")
    args = argparser.parse_args()
    text = args.text
    language = get_language(text)
    check_text(text, language)
    # print(checked)

if __name__ == "__main__":
    main()

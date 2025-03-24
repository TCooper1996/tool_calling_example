import os
from langchain_anthropic import ChatAnthropic
import dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool

dotenv.load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

secret_combination = "1234"
safe_unlocked = False

@tool
def get_safe_combination():
    """Read the safe combination from a note."""
    return secret_combination

@tool
def unlock_safe(combination: str) -> str:
    """Unlock the safe with the given combination."""
    if combination == secret_combination:
        global safe_unlocked
        safe_unlocked = True
        return "Safe unlocked!"
    else:
        return "Incorrect combination!"

tools = [get_safe_combination, unlock_safe]
llm = ChatAnthropic(api_key=api_key, model="claude-3-5-haiku-latest").bind_tools(tools)
instruction = SystemMessage(content="You are a helpful assistant. Use the tools provided to unlock the safe.")

def main():
    messages = [HumanMessage(content="Unlock the safe.")]
    while not safe_unlocked:
        response = llm.invoke([instruction, *messages])
        print(response.content)
        # Parse the response to see what tool it chose
        tool_name = response.tool_calls[0]["name"]
        tool_args = response.tool_calls[0]["args"]
        if tool_name == "get_safe_combination":
            combination = get_safe_combination(tool_input=tool_args)
            messages.append(HumanMessage(content=f"The safe combination is {combination}."))
        elif tool_name == "unlock_safe":
            result = unlock_safe(tool_args.values()[0])
            messages.append(HumanMessage(content=result))

        if safe_unlocked:
            print("Safe unlocked!")
            break
        print()


if __name__ == "__main__":
    main()
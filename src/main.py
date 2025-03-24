import os
from langchain_anthropic import ChatAnthropic
import dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from pydantic import BaseModel

dotenv.load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

secret_combination = "1234"
safe_unlocked = False

""" Tools """
# Use the tool decorate to automatically register the function as a tool
class GetSafeCombination(BaseModel):
    """Read the safe combination from a note."""

# When using the BaseModel class, you don't need a constructor,
# you can just define the fields like below
class UnlockSafe(BaseModel):
    """Unlock the safe with the given combination."""
    combination: str

""" Functions """
# Now just a normal python function
def unlock_safe(args: UnlockSafe) -> str:
    global safe_unlocked
    if args.combination == secret_combination:
        safe_unlocked = True
        return "Safe unlocked!"
    else:
        return "Incorrect combination."
    
def get_safe_combination() -> str:
    return secret_combination

# NOTE: This is a list of classes, not instances of classes (no parentheses)
tools = [GetSafeCombination, UnlockSafe]
# add tools using bind_tools
llm = ChatAnthropic(api_key=api_key, model="claude-3-5-haiku-latest").bind_tools(tools)
# Must always have a system message 
instruction = SystemMessage(content="You are a helpful assistant. Use the tools provided to unlock the safe.")

def main():
    # Models have no inherent memory so you must save each message and send them all together
    messages = [HumanMessage(content="Unlock the safe.")]
    while not safe_unlocked:
        response = llm.invoke([instruction, *messages])
        print(response.content)
        # Parse the response to see what tool it chose
        tool_name = response.tool_calls[0]["name"]
        tool_args = response.tool_calls[0]["args"]
        # look up the associated class that it selected
        action_class = [t for t in tools if t.__name__ == tool_name][0]
        # Create instance of the class with the arguments we got
        action = action_class(**tool_args)
        # Now we can use pythons BEAUTIFUL match statement to call the correct function
        match action:
            case GetSafeCombination():
                combination = get_safe_combination()
                messages.append(HumanMessage(content=f"The safe combination is {combination}."))
            case UnlockSafe(combination=combination):
                result = unlock_safe(combination)
                messages.append(HumanMessage(content=result))
            case _:
                raise ValueError(f"Unknown action: {action}")

        if safe_unlocked:
            print("Safe unlocked!")
            break
        print()


if __name__ == "__main__":
    main()
import os
from typing import ClassVar, Tuple
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
    def execute(self) -> str:
        return secret_combination


# When using the BaseModel class, you don't need a constructor,
# you can just define the fields like below
class UnlockSafe(BaseModel):
    """Unlock the safe with the given combination."""
    combination: str

    def execute(self) -> str:
        # Note: Mandatory to use the global keyword here,
        # otherwise `safe_unlocked = True` will create a new local variable
        global safe_unlocked
        if self.combination == secret_combination:
            safe_unlocked = True
            return "Safe unlocked!"
        else:
            return  "Incorrect combination."

    

# NOTE: This is a list of classes, not instances of classes (no parentheses)
tools = [GetSafeCombination, UnlockSafe]
# add tools using bind_tools
llm = ChatAnthropic(api_key=api_key, model="claude-3-5-haiku-latest").bind_tools(tools)
# Must always have a system message 
instruction = SystemMessage(content="You are a helpful assistant. Use the tools provided to unlock the safe.")

def main():
    # Models have no inherent memory so you must save each message and send them all together
    memory = [HumanMessage(content="Unlock the safe.")]
    while safe_unlocked == False:
        response = llm.invoke([instruction, *memory])
        # Add the response to the agents memory
        memory.append(response)
        print(f"Agent: {response.content[0]["text"]}")
        # Parse the response to see what tool it chose
        tool_name = response.tool_calls[0]["name"]
        tool_args = response.tool_calls[0]["args"]
        tool_id = response.tool_calls[0]["id"] # Agent will respond with a unique tool id for each tool call
        # look up the associated class that it selected
        action_class = [t for t in tools if t.__name__ == tool_name][0]
        # Create instance of the class with the arguments we got
        action = action_class(**tool_args)
        print(f"Tool Invocation: {repr(action)}")
        # Execute the action
        tool_result = action.execute()
        # add response to agents memory
        """ NOTE: This schema is strictly enforced by anthropic and other language models:
        The tool response message must be a list of dictionaries of this schema: {"type":"tool_result", "content":<content>, "tool_use_id":<tool_use_id>}
        The tool id must come from the tool_id field in the LLM response. The tool id allows the agent to know what tool this result is tied to
        """
        memory.append(HumanMessage(content=[{"type": "tool_result", "content": tool_result, "tool_use_id": tool_id}]))
        print(f"Tool Result: {tool_result}")

    print("Safe unlocked!")

if __name__ == "__main__":
    main()
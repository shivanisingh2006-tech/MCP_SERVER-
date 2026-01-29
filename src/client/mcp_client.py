import grpc
import json
import os
import sys
from openai import OpenAI

# --- IMPORT GENERATED PROTOBUF FILES ---
try:
    from ..generated import switchblade_pb2
    from ..generated import switchblade_pb2_grpc
except ImportError:
    # When running directly, add parent directory to path
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    )
    from src.generated import switchblade_pb2
    from src.generated import switchblade_pb2_grpc


# Use OpenAI's hosted API (no base_url needed)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # preferred

# ✅ OpenAI model
MODEL_NAME = "gpt-4o-mini"

# Switchblade gRPC Server Address
GRPC_SERVER_ADDR = "localhost:50051"


client = OpenAI(
    api_key=OPENAI_API_KEY
)



def get_tools_from_server(stub):
    """
    Fetches tools from Switchblade via gRPC and converts them
    to the OpenAI 'function' schema format required by the LLM.
    """
    print(f"🔌 Connecting to Switchblade ({GRPC_SERVER_ADDR})...")
    try:
        response = stub.ListTools(switchblade_pb2.Empty())
    except grpc.RpcError as e:
        print(f"❌ Connection failed: {e.details()}")
        sys.exit(1)

    openai_tools = []
    for t in response.tools:
        # Convert gRPC tool definition to OpenAI format
        try:
            # We use the input_schema_json sent by the server
            parameters = json.loads(t.input_schema_json)
        except json.JSONDecodeError:
            parameters = {}

        openai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": parameters,
                },
            }
        )

    print(
        f"✅ Discovered {len(openai_tools)} tools: {[t['function']['name'] for t in openai_tools]}"
    )
    return openai_tools


def execute_tool_on_server(stub, tool_name, args_dict):
    """
    Sends the execution request to the Switchblade server via gRPC.
    """
    print(f"⚙️  Executing tool: {tool_name}...")
    print(f"   Args: {args_dict}")

    request = switchblade_pb2.CallToolRequest(
        tool_name=tool_name, arguments_json=json.dumps(args_dict)
    )

    try:
        response = stub.CallTool(request)
        if response.is_error:
            result = f"Error: {response.error_message}"
            print(f"❌ Tool Failed: {result}")
            return result
        #if the response.json is empty then openai throw error 400 because it do not allow the none value 
        if not response.content_json:
            return"{}"

        print(f"✅ Tool Success. Result size: {len(response.content_json)} bytes")
        return response.content_json

    except grpc.RpcError as e:
        return f"RPC Connection Error: {e.details()}"


def run_chat_loop():
    # 1. Setup gRPC Channel
    channel = grpc.insecure_channel(GRPC_SERVER_ADDR)
    stub = switchblade_pb2_grpc.SwitchbladeServiceStub(channel)

    # 2. Fetch Tools
    tools = get_tools_from_server(stub)

    # 3. Prepare the "Fake" System Prompt
    system_prompt = (
        "You are Switchblade, an advanced cybersecurity agent. "
        "You have access to a dynamic set of tools. "
        "Use them to analyze, scan, and gather information when requested. "
        "Always base your answers on the tool outputs.\n"
    )

    messages = []
    print(f"\n🧠 Connected to Brain: {MODEL_NAME}")
    print("💬 Ready. Type 'quit' or 'exit' to stop.\n")

    first_turn = True

    while True:
        try:
            user_input = input("User> ")
            if user_input.lower() in ["quit", "exit"]:
                break
        except KeyboardInterrupt:
            break

        # --- FIX 1: MERGE SYSTEM PROMPT INTO FIRST USER MESSAGE ---
        if first_turn:
            full_content = f"{system_prompt}\n\nUser Query: {user_input}"
            messages.append({"role": "user", "content": full_content})
            first_turn = False
        else:
            messages.append({"role": "user", "content": user_input})

        # --- PASS 1: DECISION MAKING ---
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else "none",
            )
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            continue

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            # Append the Assistant's "intent"
            messages.append(response_message)

            # Execute all tools requested
            tool_outputs = []
            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                tool_result = execute_tool_on_server(stub, fn_name, fn_args)
                # tool_outputs.append(f"Tool '{fn_name}' returned: {tool_result}")

            # --- FIX 2: CONVERT TOOL RESULTS TO A USER MESSAGE ---
            # Instead of role='tool', we send it as role='user'
                # observation_text = "\n".join(tool_outputs)
            # messages.append(
            #     {
            #         "role": "user",
            #         "content": f"Observation from tools:\n{observation_text}",
            #     }
            # )

            # THE FIX: Create a message that OpenAI recognizes
                if tool_result is None:
                    tool_result="{}"

                messages.append({
                    "role": "tool",                 # Rule 1: Role must be 'tool'
                    "tool_call_id": tool_call.id,   # Rule 2: ID must match exactly
                    "name": fn_name,                # Rule 3: Function name must be included
                    "content": tool_result # Rule 4: Data must be a string (JSON)
                })

            # --- PASS 2: SYNTHESIS ---
            try:
                final_response = client.chat.completions.create(
                    model=MODEL_NAME, messages=messages ,tools=tools#open ai model need to again give the tools again 
                )
                msg = final_response.choices[0].message

                if msg.content is None:
                    # Fallback: summarize last tool output
                    bot_reply = "Scan completed successfully. Ports were scanned and results are available."
                else:
                    bot_reply = msg.content

                print(f"\nSwitchblade> {bot_reply}\n")

                messages.append({"role": "assistant", "content": bot_reply})

            except Exception as e:
                print(f"❌ LLM Error during synthesis: {e}")

        else:
            bot_reply = response_message.content
            print(f"\nSwitchblade> {bot_reply}\n")
            messages.append({"role": "assistant", "content": bot_reply})


if __name__ == "__main__":
    run_chat_loop()
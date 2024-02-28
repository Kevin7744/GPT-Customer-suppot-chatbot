import json
import os
import time
from flask import Flask, request, jsonify
import openai
from openai import OpenAI
import functions
from keys import OPENAI_API_KEY

# Check OpenAI version compatibility
from packaging import version

required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)


if current_version < required_version:
    raise ValueError(
        f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
    )
else:
    print("OpenAI version is compatible.")

# Create Flask app
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Create or load assistant
assistant_id = functions.create_assistant(
    client)  # this function comes from "functions.py"


# Start conversation thread
@app.route('/start', methods=['GET'])
def start_conversation():
    print("Starting a new conversation...")

    platform = request.args.get(
        'platform', 'Not Specified')  # 'Not Specified' is a default value

    thread = client.beta.threads.create()
    print(f"New thread created with ID: {thread.id}")

    # Assuming 'add_thread' function takes 'thread_id' and 'platform'
    functions.add_thread(thread_id=thread.id, platform=platform)

    return jsonify({"thread_id": thread.id})


# Generate response
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('message', '')

    if not thread_id:
        print("Error: Missing thread_id")
        return jsonify({"error": "Missing thread_id"}), 400

    print(f"Received message: {user_input} for thread ID: {thread_id}")

    # Add the user's message to the thread
    client.beta.threads.messages.create(thread_id=thread_id,
                                        role="user",
                                        content=user_input)

    # Run the Assistant
    run = client.beta.threads.runs.create(thread_id=thread_id,
                                          assistant_id=assistant_id)

    # Check if the Run requires action (function call)
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                       run_id=run.id)
        # print(f"Run status: {run_status.status}")
        if run_status.status == 'completed':
            break
        
        elif run_status.status == 'requires_action':
            tools_outputs = []
            
            # Handle the function call
            for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                if tool_call.function.name == "create_lead":
                    # Process lead creation
                    arguments = json.loads(tool_call.function.arguments)
                    output = functions.create_lead(arguments["name"], arguments["phone"],
                                                   arguments["address"], arguments["email"])
                    
                    tools_outputs.append({"tool_call_id": tool_call.id, "output": json.dumps(output)})
                
                elif tool_call.function.name == 'save_answers':
                    arguments = json.loads(tool_call.function.arguments)
                    print(arguments)
                    
                    output = functions.save_answers(
                        arguments.get('full_name', ''), 
                        arguments.get('phone', ''), 
                        arguments.get('email', ''), 
                        arguments.get('street_name', ''), 
                        arguments.get('zip_code', ''), 
                        arguments.get('city', ''), 
                        arguments.get('service_type', ''), 
                        arguments.get('ot1', ''),
                        arguments.get('ot2', ''), 
                        arguments.get('ot3', ''), 
                        arguments.get('ot4', ''),
                        arguments.get('ot5', ''), 
                        arguments.get('rc1', ''), 
                        arguments.get('rc2', ''), 
                        arguments.get('rc3', ''), 
                        arguments.get('rc4', ''), 
                        arguments.get('rc5', ''), 
                        arguments.get('pc1', ''),
                        arguments.get('pc2', ''),  
                        arguments.get('pc3', ''),  
                        arguments.get('pc4', ''),  
                        arguments.get('pc5', ''),  
                        arguments.get('pc6', ''),  
                        arguments.get('ww1', ''),  
                        arguments.get('ww2', ''),  
                        arguments.get('ww3', ''),  
                        arguments.get('ww4', ''), 
                        arguments.get('ww5', ''),  
                        arguments.get('cc1', ''), 
                        arguments.get('cc2', ''),  
                        arguments.get('cc3', ''),  
                        arguments.get('cc4', ''),  
                        arguments.get('sc1', ''), 
                        arguments.get('sc2', ''),  
                        arguments.get('sc3', ''),  
                        arguments.get('sc4', '') 
                    )

                    tools_outputs.append({"tool_call_id": tool_call.id, "output": json.dumps(output)})
                
            
            
            time.sleep(1)  # Wait for a second before checking again

            if run_status.required_action.type == 'submit_tool_outputs':
                print("Submit output")
                client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id, run_id=run.id, tool_outputs=tools_outputs)
            
    # Retrieve and return the latest message from the assistant
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[0].content[0].text.value

    print(f"Assistant response: {response}")
    return jsonify({"response": response})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

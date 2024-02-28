import json
import requests
import os
from openai import OpenAI
from prompts import assistant_instructions
from keys import OPENAI_API_KEY, AIRTABLE_API_KEY, MAKE_URL

# Init OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# Add thread to DB with platform identifier


def add_thread(thread_id, platform):
    # replace this with your Airtable Web API URL
    url = "https://api.airtable.com/v0/appCkbD804q1OaxGh/Threads"
    headers = {
        "Authorization": AIRTABLE_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "records": [{
            "fields": {
                "Thread ID": thread_id,
                "Platform": platform
            }
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            print("Thread added to DB successfully.")
        else:
            # Handle non-200 HTTP response status codes
            print(
                f"Failed to add thread: HTTP Status Code {response.status_code}, Response: {response.text}"
            )
    except Exception as e:
        # Handle exceptions like network errors, request timeouts, etc.
        print(f"An error occurred while adding the thread: {e}")

# Add lead to Airtable


def create_lead(name, phone, address, email):
    # Change this to your Airtable API URL
    url = "https://api.airtable.com/v0/appCkbD804q1OaxGh/Leads"
    headers = {
        "Authorization": AIRTABLE_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "records": [{
            "fields": {
                "Name": name,
                "Phone": phone,
                "Address": address,
                "Email": email
            }
        }]
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print("Lead created successfully.")
        return response.json()
    else:
        print(f"Failed to create lead: {response.text}")
        return ''


def save_answers(full_name, phone, email, street_name, zip_code, city,
                 service_type, 
                 ot1, ot2, ot3, ot4, ot5,  # responses for one-time cleaning
                 rc1, rc2, rc3, rc4, rc5,  # responses for regular cleaning
                 pc1, pc2, pc3, pc4, pc5, pc6,  # responses for post-construction cleaning
                 ww1, ww2, ww3, ww4, ww5,  # responses for window washing
                 cc1, cc2, cc3, cc4,  # responses for carpet cleaning
                 sc1, sc2, sc3, sc4  # responses for sofa cleaning
                 ):

    resp = requests.get(MAKE_URL, data={
        'full_name': full_name,
        'street_name': street_name,
        'zip_code': zip_code,
        'phone': phone,
        'email': email,
        'city': city,
        'service_type': service_type, 
        'ot1': ot1,
        'ot2': ot2,
        'ot3': ot3,
        'ot4': ot4,
        'ot5': ot5,
        'rc1': rc1,
        'rc2': rc2,
        'rc3': rc3,
        'rc4': rc4,
        'rc5': rc5,
        'pc1': pc1,
        'pc2': pc2,
        'pc3': pc3,
        'pc4': pc4,
        'pc5': pc5,
        'pc6': pc6,
        'ww1': ww1,
        'ww2': ww2,
        'ww3': ww3,
        'ww4': ww4,
        'ww5': ww5,
        'cc1': cc1,
        'cc2': cc2,
        'cc3': cc3,
        'cc4': cc4,
        'sc1': sc1,
        'sc2': sc2,
        'sc3': sc3,
        'sc4': sc4
    })

    if resp.ok:
        print('Saved answers successfully')
        return resp.text
    else:
        print('Failed to save responses')
        return ''


# Create or load assistant
def create_assistant(client):
    assistant_file_path = 'assistant.json'

    # If there is an assistant.json file already, then load that assistant
    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, 'r') as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data['assistant_id']
            print("Loaded existing assistant ID.")
    else:
        # If no assistant.json is present, create a new assistant using the below specifications

        # To change the knowledge document, modifiy the file name below to match your document
        # If you want to add multiple files, paste this function into ChatGPT and ask for it to add support for multiple files
        file = client.files.create(file=open("knowledge.docx", "rb"),
                                   purpose='assistants')
        
        f2 = client.files.create(file=open('site_data.txt', 'rb'), purpose='assistants')

        assistant = client.beta.assistants.create(
            # Getting assistant prompt from "prompts.py" file, edit on left panel if you want to change the prompt
            instructions=assistant_instructions,
            model="gpt-4-1106-preview",
            tools=[
                {
                    "type": "retrieval"  # This adds the knowledge base as a tool
                },
                {
                    "type": "function",  # This adds the lead capture as a tool
                    "function": {
                        "name": "create_lead",
                        "description":
                        "Capture lead details and save to Airtable.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the lead."
                                },
                                "phone": {
                                    "type": "string",
                                    "description": "Phone number of the lead."
                                },
                                "address": {
                                    "type": "string",
                                    "description": "Address of the lead."
                                },
                                "email": {
                                    "type": "string",
                                    "description": "Email of the lead"
                                }
                            },
                            "required": ["name", "phone", "address", "email"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "save_answers",
                        "description": """Capture the details of the user and the answers provided by the user a cleaning service booking and send them to a designated endpoint. 
                                        You must collect the user's personal details (full_name, phone, email, street_name, zip_code, city) before submitting the data to the endpoint.""",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "full_name": {
                                    "type": "string",
                                    "description": "Full name of the user."
                                },
                                "phone": {
                                    "type": "string",
                                    "description": "Phone number of the user."
                                },
                                "email": {
                                    "type": "string",
                                    "description": "Email address of the user."
                                },
                                "street_name": {
                                    "type": "string",
                                    "description": "Street name of the user's address."
                                },
                                "zip_code": {
                                    "type": "string",
                                    "description": "Zip code of the user's location."
                                },
                                "city": {
                                    "type": "string",
                                    "description": "City of the user's residence."
                                },
                                "service_type": {
                                    "type": "string", 
                                    "description": "Type of cleaning service, one of: 'One-time cleaning', 'Regular cleaning', 'Post-construction cleaning', 'Window washing', 'Carpet Cleaning', 'Sofa Cleaning'"
                                }, 

                                "ot1": {"type": "string", "description": "Response for one-time cleaning question: 'Which standard cleaning tasks do you require? (required to have an answer)'"},
                                "ot2": {"type": "string", "description": "Response for one-time cleaning question: 'What is the total square footage (m²) of the space that needs to be cleaned? (required to have an answer)'"},
                                "ot3": {"type": "string", "description": "Response for one-time cleaning question: 'Are there specific spots or details that need extra attention?'"},
                                "ot4": {"type": "string", "description": "Response for one-time cleaning question: 'Are there specific cleaning products we should use, for instance, for a certain type of floor?'"},
                                "ot5": {"type": "string", "description": "Response for one-time cleaning question: 'Do you also wish the windows to be washed?'"},

                                "rc1": {"type": "string", "description": "Response for regular cleaning question 1: 'Desired cleaning frequency (required to have an answer)'"},
                                "rc2": {"type": "string", "description": "Response for regular cleaning question 2: 'How often per week do you want cleaning to be done? (required to have an answer)'"},
                                "rc3": {"type": "string", "description": "Response for regular cleaning question 3: 'What is the total square footage (m²) of the space that needs to be cleaned? (required to have an answer)'"},
                                "rc4": {"type": "string", "description": "Response for regular cleaning question 4: 'What standard cleaning tasks do you expect from us?'"},
                                "rc5": {"type": "string", "description": "Response for regular cleaning question 5: 'Are there specific focus points or additional tasks you want to be executed?'"},

                                "pc1": {"type": "string", "description": "Response for post-construction cleaning question 1: 'Which standard cleaning tasks do you require?'"},
                                "pc2": {"type": "string", "description": "Response for post-construction cleaning question 2: 'What is the current condition of the spaces?'"},
                                "pc3": {"type": "string", "description": "Response for post-construction cleaning question 3: 'Are there specific spots or details that need extra attention?'"},
                                "pc4": {"type": "string", "description": "Response for post-construction cleaning question 4: 'What is the total square footage (m²) of the space that needs to be cleaned? (required to have an answer)'"},
                                "pc5": {"type": "string", "description": "Response for post-construction cleaning question 5: 'Are there specific cleaning products we should use, for instance, for a certain type of floor?'"},
                                "pc6": {"type": "string", "description": "Response for post-construction cleaning question 6: 'Are there any traces of cement grout haze?'"},

                                "ww1": {"type": "string", "description": "Response for window washing question 1: 'What is the total square footage (m²) of the space that needs to be cleaned? (required to have an answer)'"},
                                "ww2": {"type": "string", "description": "Response for window washing question 2: 'How many windows approximately need to be washed?'"},
                                "ww3": {"type": "string", "description": "Response for window washing question 3: 'How dirty are the windows currently?'"},
                                "ww4": {"type": "string", "description": "Response for window washing question 4: 'Are they mostly large or small windows?'"},
                                "ww5": {"type": "string", "description": "Response for window washing question 5: 'Are there specific cleaning products we should use for the windows?'"},

                                "cc1": {"type": "string", "description": "Response for carpet cleaning question 1: 'What is the width of the carpet you want to be cleaned? (in meters) (required to have an answer)'"},
                                "cc2": {"type": "string", "description": "Response for carpet cleaning question 2: 'What is the length of the carpet you want to be cleaned? (in meters) (required to have an answer)'"},
                                "cc3": {"type": "string", "description": "Response for carpet cleaning question 3: 'If you wish to have multiple carpets cleaned, please specify the total number of carpets to be cleaned here.'"},
                                "cc4": {"type": "string", "description": "Response for carpet cleaning question 4: 'If you have multiple carpets with different dimensions that need cleaning, please specify the dimensions of each carpet here.'"},

                                "sc1": {"type": "string", "description": "Response for sofa cleaning question 1: 'How many sofas do you want to be cleaned? (required to have an answer)'"},
                                "sc2": {"type": "string", "description": "Response for sofa cleaning question 2: 'How many seating places do the sofa(s) you want to be cleaned have? (required to have an answer)'"},
                                "sc3": {"type": "string", "description": "Response for sofa cleaning question 3: 'If you have multiple sofas with different seating arrangements to be cleaned, please specify the details of each sofa here.'"},
                                "sc4": {"type": "string", "description": "Response for sofa cleaning question 4: 'Is it a corner sofa?'"}
                            },
                            "required": [
                                "full_name", "phone", "email", "street_name", "zip_code", "city"
                            ]
                        }
                    }
                }

            ],
            file_ids=[file.id, f2.id])

        # Create a new assistant.json file to load on future runs
        with open(assistant_file_path, 'w') as file:
            json.dump({'assistant_id': assistant.id}, file)
            print("Created a new assistant and saved the ID.")

        assistant_id = assistant.id

    return assistant_id



if __name__ == '__main__':
    save_answers('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '')
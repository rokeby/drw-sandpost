from flask import Flask, jsonify, request
import csv
import os
import os.path
import re
import random
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timedelta
import pickle
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

dirname = os.path.dirname(__file__)

package = ""

app = Flask(__name__)

client = OpenAI()
api_key = os.getenv("OPENAI_API_KEY")

# Email configurations
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
# RECIPIENT_EMAILS = ["weil.flora@gmail.com"]  # Change this to the recipient's email address
RECIPIENT_EMAILS = ["zhexi@mit.edu"]  # Change this to the recipient's email address
BCC_EMAIL = ["gary.zhexi.zhang@gmail.com"]

# Function to load data from a JSON file
def load_json_data(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
        if not content.strip():
            print(f"Error: The file {file_path} is empty.")
            return None
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Error: The file {file_path} contains invalid JSON. {str(e)}")
            return None
    return data

# Function to load all data from the "data" directory in the root folder
def load_data():
    data_files = {}
    dirname = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # Root directory
    data_dir = os.path.join(dirname, 'DRW-server/data')  # "data" directory in the root folder

    # List all JSON files in the "data" directory
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            key = os.path.splitext(filename)[0]  # Filename without extension
            file_path = os.path.join(data_dir, filename)
            print(f"Loading file: {file_path}")
            data = load_json_data(file_path)
            if data is not None:
                data_files[key] = data
            else:
                print(f"Skipping empty or invalid file: {file_path}")
    
    return data_files

# Call the function to load data
data = load_data()

atmosphere = data.get('atmosphere', {})
creatures = data.get('creatures', {})
people = data.get('people', {})
scenes = data.get('scenes', {})
sounds = data.get('sounds', {})


# Function to randomly select a description from a dictionary
def get_random_object(data_dict):
    if data_dict:
        return random.choice(list(data_dict.values()))
    return None

# def get_random_object(data_dict):
#     if isinstance(data_dict, dict) and data_dict:
#         # Randomly select a key from the dictionary
#         selected_key = random.choice(list(data_dict.keys()))
#         # Get the corresponding object and its description
#         selected_object = data_dict[selected_key]
#         # Return both the selected object and its description
#         return {
#             "name": selected_key,
#             "description": selected_object.get("description", "")
#         }
#     return None

# Cache management functions
CACHE_FILE = 'cache.pkl'

def load_cache():
    if os.path.isfile(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            return pickle.load(f)
    return None

def save_cache(data):
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(data, f)

def send_email(package):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ", ".join(RECIPIENT_EMAILS)
    msg['Subject'] = f""" {package['haiku']} """

    body = f"""
    <p><i>{package['interpretation']}</i></p>
    <p>{datetime.now()}</p>
    <p>Unsubscribe link</p>

    """

    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAILS + BCC_EMAIL, msg.as_string())

def generate_message():

    print("running generate_message()")
    print("\n")

    # Create the package with randomized fragments
    package = {
        "fragments": {
            "atmosphere": get_random_object(atmosphere),
            "creature": get_random_object(creatures),
            "person": get_random_object(people),
            "scene": get_random_object(scenes),
            "sound": get_random_object(sounds)
        }
    }

    for key, value in package["fragments"].items():
        if value and isinstance(value, dict):
            print(f"{key.capitalize()}: {value.get('name', 'No name field')}")
        else:
            print(f"{key.capitalize()}: None")

    print("\n")
    print("reading fragments")

    prompt = f"take these fragments and assemble loose, ethnographic journal entry of what you have seen today. less than 80 words. no detail is too small or mundane. describe what you did today. your language is practical, you are scribbling them down at the end of the day, inspired but terse and tired {package}"

    completion = client.chat.completions.create(
        model="gpt-4o",
        # model="gpt-3.5-turbo",
        # model="gpt-4",
        messages=[
            {"role": "system", "content": "you are a weary anthropologist making daily notes, studying emergent forms of agriculture, bio-engineering, geological mutations in a desert landscape. you have a deep knowledge of ancient hydrology. there is no need to separate notes into sections. do not repeat the names of objects exactly"},
            {"role": "user", "content": prompt}
        ]
    )

    poem = completion.choices[0].message.content

    package['haiku'] = str(poem.replace("\n", " "))

    print("compiled fragments", package['haiku'])
    print("constructing narrative")

    prompt = f"make an alternative version of these notes, drawing on desert meterology, geoengineering, ecology. there's no need to copy every aspect, but make up new details for what you pick up. describe today's events in order, no detail is too small. days are often are mundane. you are NOT POETIC, almost autistically dry. madness is teasing you and at times you dream and hallucinate, it is harder and harder to tell what is reality; do not mention this explicitly. less than 150 words {poem}"

    completion = client.chat.completions.create(
        # model="gpt-4o",
        # model="gpt-3.5-turbo",
        model="gpt-4",
        messages=[
            {"role": "system", "content": "you are a consultant anthropologist working on exploration for new minerals for climate technology. you are weary. write your internal corporate report in the style of Cormac McCarthy."},
            {"role": "user", "content": prompt}
        ]
    )



    # prompt = f"interpret these notes and make observations of your own. who could she be? she's like an alien, trying to observe you from the land. you write to her in the tone of a curious child, she is funny to you, but you also pity her a little, down there. don't use gendered terms, refer to her only as stranger. less than 100 words {poem}"

    # completion = client.chat.completions.create(
    #     # model="gpt-4o",
    #     # model="gpt-3.5-turbo",
    #     model="gpt-4",
    #     messages=[
    #         {"role": "system", "content": "you are the wind, witnessing this weary ethnographer's landbound struggle to understand your world from their terrestrial dimension. this is your world, you float freely. You write in first person but use I sparingly. your style is curious but a little tentative. your language is never flowery, using adjectives sparingly."},
    #         {"role": "user", "content": prompt}
    #     ]
    # )

    interpretation = completion.choices[0].message.content
    package['interpretation'] = str(interpretation.replace("\n", " "))

    print("completed interpretation", package['interpretation'])

    # Save the generated message with a timestamp
    cache_data = {
        'timestamp': datetime.now(),
        'message': package
    }
    save_cache(cache_data)

    print("saved package as cache_data")
    print("\n\n")


    # Send the package via email
    # print(datetime.now(), "sending package as email to", RECIPIENT_EMAILS, BCC_EMAIL)
    # send_email(package)

    return package

def get_oracle():
    cache_data = load_cache()
    if cache_data:
        cache_timestamp = cache_data['timestamp']
        if datetime.now() - cache_timestamp < timedelta(seconds=1):
            # Serve the cached message
            print("initiated", datetime.now(), "\n cached message less than 1 second old,", "\n generated at:", cache_timestamp, "\n returning cached message \n", cache_data["message"])
            print("\n")
            return cache_data['message']
        else:
            print(datetime.now(), "cached message more than a second old, (", cache_timestamp, ") generating new message")
            print("\n")
            package = generate_message()
            print(datetime.now(), "\n\n")
            print("cached message: \n\n", package['haiku'], "\n\n")
            print("interpretation: \n\n", package['interpretation'], "\n")
    else:
        print(datetime.now(), "no cache message found! generating new message.")
        print("\n")
        package = generate_message()
        print(datetime.now(), "\n", "cached message:", package)        


get_oracle()

@app.route('/')
def home():
    package = load_cache()
    return package

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, use_reloader=False)


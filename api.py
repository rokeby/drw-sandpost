from flask import Flask, jsonify, request
import csv
import os
import os.path
import re
import random
import json
import requests
import logging
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timedelta, timezone
import pickle
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

logging.basicConfig(level=logging.INFO)

package = ""

app = Flask(__name__)

client = OpenAI()
api_key = os.getenv("OPENAI_API_KEY")

# Email configurations
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
BCC_EMAIL = [""]

# Directory paths
dirname = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # Root directory
data_dir = os.path.join(dirname, 'DRW-server/data')  # "data" directory in the root folder

# File paths
MAIL_LIST_FILE = os.path.join(data_dir, "mail-list")
UNSUBSCRIBE_LIST_FILE = os.path.join(data_dir, "unsubscribe-list")
ARCHIVE_FILE = os.path.join(data_dir, "message_archive.json")

def ensure_file_exists(file_path, initial_content=None):
    """Ensure the file exists; create it if it doesn't, with optional initial content."""
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            if initial_content:
                f.write(initial_content + '\n')
        print(f"Created file: {file_path}")

def get_recipient_emails(mail_list_file, unsubscribe_list_file):
    """Read the mail list and remove any emails present in the unsubscribe list."""
    # Ensure mail-list and unsubscribe-list files exist
    ensure_file_exists(mail_list_file, initial_content="gary.zhexi.zhang@gmail.com")
    ensure_file_exists(unsubscribe_list_file)

    try:
        # Read emails from the mail list file
        with open(mail_list_file, 'r') as f:
            mail_list = set(line.strip() for line in f if line.strip())

        # Read emails from the unsubscribe list file
        with open(unsubscribe_list_file, 'r') as f:
            unsubscribe_list = set(line.strip() for line in f if line.strip())

        # Remove any emails from the mail list that are in the unsubscribe list
        filtered_mail_list = list(mail_list - unsubscribe_list)

        # Update the mail-list file with the filtered emails
        with open(mail_list_file, 'w') as f:
            for email in filtered_mail_list:
                f.write(email + '\n')

        return filtered_mail_list

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

def send_email(package):
    # Get the filtered recipient emails
    recipient_emails = get_recipient_emails(MAIL_LIST_FILE, UNSUBSCRIBE_LIST_FILE)
    
    if not recipient_emails:
        print("No valid recipient emails found. Exiting...")
        return
    
    # Create the MIMEMultipart object for the email message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ", ".join(recipient_emails)
    msg['Subject'] = f"sandpost, {datetime.now(timezone.utc)}"

    # Construct the email body using HTML
    body = f"""
    <p><i>{package['report']}</i></p>
    <p>{datetime.now()}</p>
    <p><a href="https://unsubscribe.link">unsubscribe from sandpost</a></p>
    """

    # Attach the HTML body to the email message
    msg.attach(MIMEText(body, 'html'))

    try:
        # Connect to the SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Start TLS encryption
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)  # Login to the server
            # Send the email to the recipients, including BCC
            server.sendmail(
                EMAIL_ADDRESS, 
                recipient_emails + BCC_EMAIL, 
                msg.as_string()
            )
        logging.info(f"Successfully sent email to {recipient_emails + BCC_EMAIL}")

    except Exception as e:
        
        logging.error(f"An error occurred while sending email: {e}")

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

    # List all JSON files in the "data" directory
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            key = os.path.splitext(filename)[0]  # Filename without extension
            file_path = os.path.join(data_dir, filename)
            print(f"Loading file: {filename}")
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

def generate_message():

    print("generating new message at", datetime.now(), "\n")

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

    print("\nreading fragments \n")

    prompt = f"take these fragments and assemble loose, ethnographic journal entry of what you have seen today. less than 80 words. no detail is too small or mundane. your language is practical, obsessive but terse {package}"

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

    package['fragment'] = str(poem.replace("\n", " "))

    # print("compiled fragments:", package['fragment'], "\n")
    print("constructing report")

    prompt = f"make an alternative version of these notes, drawing on desert meterology, geoengineering, ecology. further elaborate on the details you pick up. describe today's events in order, no detail is too small. days are often are mundane. you are NOT POETIC, almost autistically dry. madness is closing in on you, it is harder and harder to tell words and reality apart (do not mention this explicitly). less than 150 words. use html formatting and spacing insanely to space and style your transmission, based on the content. end on a set of geographical coordinates, unmarked, relevant to your message. do not use a title. {poem}"

    completion = client.chat.completions.create(
        model="gpt-4o",
        # model="gpt-3.5-turbo",
        # model="gpt-4",
        messages=[
            {"role": "system", "content": "you are an anonymous consultant anthropologist working on exploration for new minerals, potentially for geo-engineering technology for a chinese firm. you have an interest in mysticism. your remarks are specific, do not make broad new-age sentiments, there is no need to conclude your remarks. you are weary. write your internal corporate report, in the style of the CCRU, Nick Land, Haruki Murakami. today's date tell's you the season."},
            {"role": "user", "content": prompt}
        ]
    )

    report = completion.choices[0].message.content
    package['report'] = str(report.replace("\n", " "))

    # print("completed report", package['report'])

    # Save the generated message with a timestamp
    cache_data = {
        'timestamp': datetime.now(),
        'message': package
    }
    save_cache(cache_data)

    print("saved package as cache_data")

    return package

def get_oracle():
    cache_data = load_cache()
    if cache_data:
        cache_timestamp = cache_data['timestamp']
        # timedelta set at 1 second for testing, should be 24h! 
        if datetime.now() - cache_timestamp < timedelta(seconds=1): 
            # Serve the cached message
            print("cached message less than 1 second old,", "\n generated at:", cache_timestamp, "\n returning cached message \n", cache_data["message"])
            print("\n")
            return cache_data['message']
        else:
            print("\ncached message more than a second old")
            package = generate_message()
            print(datetime.now(), "\n")
            print("cached message: \n\n", package['fragment'], "\n")
            print("report: \n\n", package['report'], "\n")
            append_to_archive(package)
            send_email(package)
    else:
        print("no cache message found! generating new message at", datetime.now())
        print("\n")
        package = generate_message()
        print(datetime.now(), "\n", "cached message:", package)        
        append_to_archive(package)

def append_to_archive(package):
    """Append the new package to the archive file."""
    ensure_file_exists(ARCHIVE_FILE, initial_content="")
    
    try:
        # Load the existing archive data
        with open(ARCHIVE_FILE, 'r') as f:
            try:
                archive_data = json.load(f)
                if not isinstance(archive_data, list):
                    archive_data = []  # Initialize as an empty list if it's not a list
            except json.JSONDecodeError:
                archive_data = []  # Initialize as an empty list if the file is empty or invalid

        # Add a timestamp to the package and append it to the archive
        archive_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": package
        }
        archive_data.append(archive_entry)
        
        # Save the updated archive data
        with open(ARCHIVE_FILE, 'w') as f:
            json.dump(archive_data, f, indent=4)
        logging.info("Appended new message to the archive.")
    
    except Exception as e:
        logging.error(f"An error occurred while archiving the message: {e}")

get_oracle()

@app.route('/')
def home():
    package = load_cache()
    if package:
        return jsonify(package['message'])
    return jsonify({"error": "No data available"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, use_reloader=False)


# In this script we devide a document into chunks, send them to a GPT to see if we can extract possible votings, and then write out the results to json
import os
import json
import time

# Import other needed libraries
from langchain import PromptTemplate, LLMChain
from langchain.llms import Ollama

# Set up variables
folder_path = "data/voting-test/"
chunks_folder_path = f"{folder_path}chunks/"
votes_folder_path = f"{folder_path}votes/"
overwrite = False

# Import the voting dictionary for pre-selection
import voting_dictionary
voting_dictionary = voting_dictionary.minimal_voting_dictionary
    
# Create votes folder if it doesn't exist
if not os.path.exists(votes_folder_path):
    os.makedirs(votes_folder_path)

files = []
files_in_root = [f.path for f in os.scandir(
    chunks_folder_path) if f.is_file() and f.name.endswith(".json")]
for file in files_in_root:
    files.append(file)

print(f"Found {len(files)} json chunks files in the {chunks_folder_path} folder")

for file in files:
    print(file)

if (len(files) == 0):
    print(f"No json chunks files found in the {chunks_folder_path} folder. Please add some (using the other scripts) and try again.")
    exit()

# Import the parties
party_file = f"{folder_path}parties.json"
parties = []
parties_text = ""
with open(party_file) as json_file:
    parties = json.load(json_file)
    for party in parties:
        parties_text += f"{party['abbreviation']}, "

print(f"Parties used in prompt: {parties_text}")

# Set up LLM and prompt
prompt_template = """
Je bekijkt een stuk tekst uit een gemeenteraadsvergadering of ander gemeentelijk document. Je gaat kijken of je daar het stemgedrag van verschillende partijen uit kunt destilleren. Kijk of je in de onderstaande context een stemming of motie kunt vinden. Let vooral op woorden als raadsvoorstel of motie, of termen als stemmen en aangenomen. Als je denkt dat het om een stemming of motie gaat, geef dan de stemming terug als een json object met de volgende structuur:
- title: de titel van de stemming
- vote: de (tekstuele) omschrijving van de uitslag van de stemming
- pro: de partijen die voor hebben gestemd (in een array)
- against: de partijen die tegen hebben gestemd (in een array)
Kun je geen stemming vinden, geef dan Null (met hoofdletter) terug.
Is er sprake van een situatie waar alleen voor- of tegenstanders worden genoemd, of alle partijen unaniem stemmen, vul de pro of against array dan met deze partijen:
{parties_text}
Pak maximaal één stemming per context. Als je meerdere stemmingen vindt, pak dan de eerste.

MAKE SURE TO ANSWER WITH A VALID JSON OBJECT and only that AS DESCRIBED ABOVE! THIS IS CRITICAL. So no surrounding text, just the json object. If you don't, the script will fail.

Context: 
{context}
"""

prompt_template_english = """
You are examining a piece of text from a municipal council meeting or other municipal document. You are going to see if you can extract the voting behavior of different parties from it. Check if you can find a vote or motion in the context below. Pay attention to words like "raadsvoorstel" (council proposal) or "motie" (motion), or terms like "stemmen" (vote) and "aangenomen" (adopted). If you think it is a vote or motion, return the vote as a JSON object with the following structure:

- title: the title of the vote
- vote: the textual description of the vote result
- pro: the parties that voted in favor (in an array)
 - against: the parties that voted against (in an array) If you cannot find a vote, return Null (with a capital N). 
If there is a situation where only supporters or opponents are mentioned, or all parties vote unanimously, fill the pro or against array with these parties:
{parties_text} 
Retrieve a maximum of one vote per context. If you find multiple votes, take the first one.
Context:
{context}

MAKE SURE TO ANSWER WITH A VALID JSON OBJECT and only that object AS DESCRIBED ABOVE! THIS IS CRITICAL. So no surrounding text! Also no code marks (```). Just the json object. If you do provide text outside the object, the answer will be rejected.
"""

llm = Ollama(model="vicuna")

prompt = PromptTemplate(template=prompt_template_english, input_variables=["context", "parties_text"])

llm_chain = LLMChain(
    llm=llm,
    prompt=prompt
)

# Loop over files
for file in files:
    # Check if the file has already been processed
    file_name = file.split("/")[-1]
    # Cut off the .json extension
    file_name = file_name[:-5]
    full_file_name = f"{votes_folder_path}{file_name}"
    print(f"Checking if file {full_file_name} already exists")
    if (os.path.exists(full_file_name) and not overwrite):
        print(f"File {file_name} already exists in the votes folder, skipping")
        continue

    # Set up variables
    print(f"Processing chunks from file {file}")
    file_splits = []
    voting_results = []
    amount_containing_voting_term = 0
    to_llm = []

    # Open the file
    with open(file) as json_file:
        data = json.load(json_file)
        # Get the chunks from the file
        for chunk in data:
            file_splits.append(chunk)

        print(f"Found {len(file_splits)} chunks in this file to process")

    # Loop over chunks
    for index, split in enumerate(file_splits):
        # Get the page content from the split
        split_content = split["text"]

        # Check if the split contains any of the voting dictionary terms
        contains_voting_term = False
        for term in voting_dictionary:
            if (term in split_content):
                contains_voting_term = True
                break
        
        # If the split doesn't contain any voting terms, skip it
        if (not contains_voting_term):
            continue

        # Add the split to the to_llm array
        to_llm.append(split)
    
    print(f"Found {len(to_llm)} chunks containing voting terms (out of {len(file_splits)} total chunks)")

    for llm_index, llm_split in enumerate(to_llm):
        llm_split_content = llm_split["text"]
        print(f"Processing chunk {llm_index} of {len(to_llm)} for file {file_name}")
        # Run the LLM chain
        result = llm_chain({"context": llm_split_content, "parties_text": parties_text})

        if (result):
            result_text = result["text"]
            result_text = result_text.replace("\n", "")  
            if (result_text != "Null"):
                print(result_text)
                voting_results.append(result_text)
            else:
                print("No voting found")
        
        # Sleep to prevent rate limiting
        time.sleep(2)


    parsed_data = []
    for item in voting_results:
        try:
            parsed_item = json.loads(item)
            parsed_data.append(parsed_item)
        except json.JSONDecodeError:
            continue
    print(parsed_data)

    # Write out the voting results to json
    with open(f"{votes_folder_path}/{file_name}-vicuna.json", 'w') as outfile:
        json.dump(parsed_data, outfile, indent=4)

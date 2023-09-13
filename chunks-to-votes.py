# In this script we devide a document into chunks, send them to a GPT to see if we can extract possible votings, and then write out the results to json
import os
import json

# Import other needed libraries
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI

# Import the keys and url from the constants file
import constants
os.environ["OPENAI_API_KEY"] = constants.APIKEY
os.environ["OPENAI_APIKEY"] = constants.APIKEY

# Set up an array of files to add to Weaviate
folder_path = "data/voting-test/"
chunks_folder_path = f"{folder_path}chunks/"
votes_folder_path = f"{folder_path}votes/"

# Create votes folder if it doesn't exist
if not os.path.exists(votes_folder_path):
    os.makedirs(votes_folder_path)

files = []
files_in_root = [f.path for f in os.scandir(
    chunks_folder_path) if f.is_file() and f.name.endswith(".json")]
for file in files_in_root:
    files.append(file)

print(f"Found {len(files)} josn chunks files in the {chunks_folder_path} folder")

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

Context: 
{context}
"""

llm = ChatOpenAI(model="gpt-4")

prompt = PromptTemplate(template=prompt_template, input_variables=["context", "parties_text"])

llm_chain = LLMChain(
    llm=llm,
    prompt=prompt
)

# Loop over files
for file in files:
    # Set up variables
    print(f"Processing chunks from file {file}")
    file_splits = []
    voting_results = []
    file_name = file.split("/")[-1]

    # Open the file
    with open(file) as json_file:
        data = json.load(json_file)
        # Get the chunks from the file
        for chunk in data:
            file_splits.append(chunk)

        print(f"Found {len(file_splits)} chunks in total to process")

    # Loop over chunks
    for split in file_splits:
        # Get the page content from the split
        split_content = split["text"]

        # Run the LLM chain
        result = llm_chain({"context": split_content, "parties_text": parties_text})
        # Delete newlines from the result
        if (result):
            result_text = result["text"]
            result_text = result_text.replace("\n", "")  
            if (result_text != "Null"):
                print(result_text)
                voting_results.append(result_text)
            else:
                print("No voting found")

    print(voting_results)

    # Write raw results
    with open(f"{votes_folder_path}/{file_name}-raw.json", 'w') as outfile:
        json.dump(voting_results, outfile, indent=4)

    parsed_data = [json.loads(item) for item in voting_results]
    print(parsed_data)

    # Write out the voting results to json
    with open(f"{votes_folder_path}/{file_name}.json", 'w') as outfile:
        json.dump(parsed_data, outfile, indent=4)

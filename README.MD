# TID - GGG vote extractor
This tool uses text splitting and a large language model to check documents for voting behavior. It takes a folder of documents, extracts the political entities from said documents and parses the noted down voting behavior into a machine readable format.

## Requirements
The vote extractor is written in Python. It requires a newer version of python3 and the packages listed in the requirements.txt file. To install the requirements, run the following command in the root directory of the project:
```
pip install -r requirements.txt
```
It can be useful to work with a virtual environment manager here, such as conda, to avoid conflicts wi th other python projects and bloated systems. 

## OpenAI key
Some of the scripts require an OpenAI key to access the OpenAI API. Save the key in a file named `constants.py` as follows:
```
APIKEY = "your-key-here"
```
Do NOT commit that file. 

## Scripts
As for now, the project contains several scripts that all do one part of the process. Later they can be merged into one pipeline, but for now this allows easy debugging and testing of the different parts. Make sure to run them in this order.

- `text-to-chunks.py` uses langchains text splitters to split a document into chunks. It takes a folder of documents and outputs a folder of chunks (one json per file) in the same folder.
- `get-entities.py` reads a folder of these chunks and tries to extract all political parties from the folder. It then writes a json file with all the parties and their aliases to the same folder.
- `chunks-to-votes.py` reads a folder of chunks and the parties json and tries to extract all voting behavior from the chunks. It then writes a folder with the voting behavior per file to the same folder.
- `parse-votes.py` reads all the voting files and outputs a csv with all the votes.
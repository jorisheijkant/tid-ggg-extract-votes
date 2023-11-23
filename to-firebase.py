# Import a json and push the contents to firebase
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import sys

# Get the path to the json file
json_file_path = "data/voting-test/votes/test_doc.json"
municipality = "helmond"

# Open the json file
votes = []
with open(json_file_path) as json_file:
    data = json.load(json_file)
    # Get the chunks from the file
    for chunk in data:
        votes.append(chunk)

# Use a service account
cred = credentials.Certificate('firebase-admin.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

# Just check if the db is working
doc_ref = db.collection(u'municipalities').document(u'helmond')
doc = doc_ref.get()
if doc.exists:
    print(f"Document data: {doc.to_dict()}")

# Loop over the votes
for index, vote in enumerate(votes):
    # Add the vote to the db
    doc_ref = db.collection(u'municipalities').document(u'helmond').collection(u'votes').document(str(index))
    doc_ref.set(vote)
    print(f"Added vote {index} to the db")

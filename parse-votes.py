import os
import json
import csv

# Set folder path
folder_path = "data/voting-test/"
results_path = f"{folder_path}votes/"
files = []
files_in_root = [f.path for f in os.scandir(results_path) if f.is_file() and f.name.endswith(".json") and not f.name.endswith("-raw.json")]
for file in files_in_root:
    files.append(file)

print(f"Found {len(files)} json chunks files in the {results_path} folder")

for file in files:
    print(file)

if (len(files) == 0):
    print(f"No json chunks files found in the {results_path} folder. Please add some (using the other scripts) and try again.")
    exit()

# Loop over files and concatenate everything into a single votes array
votes = []
for file in files:
    with open(file) as json_file:
        votes += json.load(json_file)

# Write votes to csv
with open(f"{folder_path}voting-results.csv", 'w') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(["subject", "vote", "pro", "against"])
    for vote in votes:
        pro_string = ""
        against_string = ""
        for pro in vote["pro"]:
            pro_string += f"{pro}, "
        for against in vote["against"]:
            against_string += f"{against}, "
        writer.writerow([vote["title"], vote["vote"], pro_string, against_string])
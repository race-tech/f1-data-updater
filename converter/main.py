from datetime import date

import requests
from pathlib import Path
import pdfplumber
import json
import sys

endpoint = "https://www.fia.com/sites/default/files/"

files = {
    "quali_classification": "f1_q0_timing_qualifyingsessionprovisionalclassification_v01.pdf",
}

def download_files(year: int, round: int, country: str) -> str:
    # Format the key to the following format:
    # year_round_country
    # Note: the round is a 2 digit number
    key = f"{year}_{round:02d}_{country}"

    # Download the files
    for file in files:
        complete_url = endpoint + key + "_" + files[file]

        # Get the file
        resp = requests.get(complete_url)

        # Save the file
        if resp.status_code == 200:
            print(complete_url + " downloaded")
            filepath = Path(f"data/{key}_{file}.pdf")
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_bytes(resp.content)
        else:
            print(f"Error: {resp.status_code}")
            exit(1)

    # Job done
    print("Files downloaded")
    return key

def convert_quali_classification(key: str, year: int, round: int):
    fn = f"data/{key}_quali_classification.pdf"

    pdf = pdfplumber.open(fn)
    page = pdf.pages[0]

    tables = page.extract_tables()

    file = Path(f"csv/{year}_{round}_quali_classification.csv")
    file.parent.mkdir(parents=True, exist_ok=True)

    # Remove 4th and 5th element of each row
    tables[0] = [row[:3] + row[5:] for row in tables[0]]

    file.write_text(",".join(["pos", "no", "driver", "entrant", "q1", "laps", "%", "time", "q2", "laps", "time", "q3", "laps", "time"]) + "\n")
    for row in tables[0]:
        file.write_text(",".join(row) + "\n")

    print("CSV file created for quali classification")
    return

if __name__ == "__main__":
    # Get round number and circuit contry from stdin arguments
    round = int(sys.argv[1])
    country = sys.argv[2]
    today = date.today()

    # Load contries.json file
    file = open("countries.json", "r")
    countries = json.load(file)

    # Find the country in the countries.json list
    code = None
    for c in countries:
        if c["name"] == country:
            # Lowercase the country code
            code = c["code"].lower()
            break

    # If the country is not found, exit
    if code is None:
        print("Country not found")
        exit(3)

    print("Country found: " + code)

    try :
        key = download_files(today.year, round, code)
        convert_quali_classification(key, today.year, round)
    except Exception as e:
        print(e)
        exit(1)

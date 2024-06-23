import requests
from pathlib import Path

endpoint = "https://www.fia.com/sites/default/files/"

files = [
    "f1_q0_timing_qualifyingsessionprovisionalclassification_v01.pdf",
]

def download_files(year: int, round: int, country: str):
    # Format the key to the following format:
    # year_round_country
    # Note: the round is a 2 digit number
    key = f"{year}_{round:02d}_{country}"

    # Download the files
    for file in files:
        complete_url = endpoint + key + "_" + file
        print(complete_url)

        # Get the file
        resp = requests.get(complete_url)

        # Save the file
        if resp.status_code == 200:
            filepath = Path(f"data/{key}_{file}")
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_bytes(resp.content)
        else:
            print(f"Error: {resp.status_code}")

    return

if __name__ == "__main__":
    download_files(2024, 10, "esp")

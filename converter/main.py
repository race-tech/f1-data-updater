from datetime import date
from re import sub
from urllib.request import urlopen
from bs4 import BeautifulSoup
from bs4.element import Tag

import requests
from pathlib import Path
import json
import sys

from parser.parse_quali import parse_quali_final_classification
from parser.parse_driver_championship import parse_driver_championship
from parser.parse_constructor_championship import parse_constructor_championship
from parser.parse_race_classification import parse_race_final_classification
from parser.parse_race_history_chart import parse_race_history_chart
from parser.parse_race_lap_chart import parse_race_lap_chart
from parser.parse_race_pit_stops import parse_race_pit_stop

from parser.parse_sprint_history_chart import parse_sprint_history_chart
from parser.parse_sprint_classification import parse_sprint_final_classification
from parser.parse_sprint_lap_chart import parse_sprint_lap_chart

base = "https://www.fia.com"
endpoint = "https://www.fia.com/events/fia-formula-one-world-championship"

titles = {
    "RACE": {
        "race_classification": [
            "Race Provisional Classification",
            "Provisional Classification",
            "Classification",
            "Provisional Race Classification"
        ],
        "race_lap_chart": [
            "Race Lap Chart",
            "Lap Chart"
        ],
        "drivers_championship": [
            "Drivers Championship",
            "Drivers' Championship"
        ],
        "constructors_championship": [
            "Constructors Championship",
            "Drivers' Championship  Constructors Championship"
        ],
        "race_pit_stops": [
            "Race Pit Stop Summary",
            "Pit Stop Summary"
        ],
        "race_history_chart": [
            "History Chart"
        ]
    },
    "QUALIFYING": {
        "quali_classification": ["Provisional Classification", "Classification"]
    },
    "SPRINT RACE": {
        "sprint_classification": ["Provisional Classification", "Sprint Provisional Classification", "Classification"],
        "sprint_lap_chart": ["Sprint Lap Chart", "Lap Chart"],
        "sprint_history_chart": [
            "History Chart",
            "Sprint History Chart"
        ]
    }
}

entrant_mapping = {
    "Oracle Red Bull Racing": "Red Bull",
    "McLaren Formula 1 Team": "McLaren",
    "Mercedes-AMG PETRONAS F1 Team": "Mercedes",
    "Aston Martin Aramco F1 Team": "Aston Martin",
    "Scuderia Ferrari": "Ferrari",
    "Williams Racing": "Williams",
    "BWT Alpine F1 Team": "Alpine F1 Team",
    "MoneyGram Haas F1 Team": "Haas F1 Team",
    "Visa Cash App RB F1 Team": "RB F1 Team",
    "Stake F1 Team Kick Sauber": "Sauber",
}

def download_files(year: int, race_name: str, is_sprint: bool):
    # Format the key to the following format:
    # year_round_country
    # Note: the round is a 2 digit number
    complete_url = endpoint + f"/season-{year}/{race_name}/eventtiming-information"
    print("Event timing url: " +complete_url)
    page = urlopen(complete_url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # Select the div.content > div.middle
    content = soup.find("div", class_="content")

    if not isinstance(content, Tag):
        print("Error: content not found")
        exit(1)

    middle = content.find("div", class_="middle")

    if not isinstance(middle, Tag):
        print("Error: middle not found")
        exit(1)

    files_url = {
        "RACE": [],
        "QUALIFYING": [],
        "SPRINT RACE": [],
    }
    current_header = ""

    for div in middle.findChildren():
        if not isinstance(div, Tag):
            continue

        b_tag = div.find("b")
        strong_tag = div.find("strong")

        if div.name == "p":
            if b_tag is not None:
                current_header = ""

                for header in files_url:
                    if header == b_tag.getText(strip=True):
                        current_header = header
                        break
            elif strong_tag is not None:
                current_header = ""

                for header in files_url:
                    if header == strong_tag.getText(strip=True):
                        current_header = header
                        break

        classes = div.get("class")

        if current_header == "":
            continue

        if classes is None or classes[0] != 'for-documents':
            continue

        a = div.find("a")

        if not isinstance(a, Tag):
            print("Error: a tag not found")
            exit(1)

        title_div = div.find("div", class_="title")

        if not isinstance(title_div, Tag):
            print("Error: title_div not found")
            exit(1)

        url = a.get("href")
        title = title_div.text

        print(f"Found: {current_header} - {title}")
        files_url[current_header].append((title, url))

    print("----- Files found -----")

    for header in files_url:
        for files in files_url[header]:
            fn = None

            for f in titles[header]:
                if files[0] in titles[header][f]:
                    fn = f
                    break

            if fn is None:
                print(f"Skipping: {files[0]}")
                continue

            dl_url = base + files[1]

            print(f"Downloading: {dl_url} to {fn}.pdf")

            resp = requests.get(dl_url)

            if resp.status_code != 200:
                print(f"Error could not download: {dl_url} - {resp.status_code}")
                exit(1)

            filepath = Path(f"data/{fn}.pdf")
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_bytes(resp.content)

def create_quali_classification():
    data = parse_quali_final_classification("data/quali_classification.pdf")
    data.to_csv("csv/quali_classification.csv", index=False)

    print("----- CSV file created for quali classification -----")
    return

def create_sprint_history_chart():
    data = parse_sprint_history_chart("data/sprint_history_chart.pdf")
    data.to_csv("csv/sprint_history_chart.csv", index=False)

    print("----- CSV file created for sprint laps analysis -----")
    return

def create_sprint_classification():
    data = parse_sprint_final_classification("data/sprint_classification.pdf")
    data.to_csv("csv/sprint_classification.csv", index=False)

    print("----- CSV file created for sprint classification -----")
    return

def create_sprint_lap_chart():
    data = parse_sprint_lap_chart("data/sprint_lap_chart.pdf")
    data.to_csv("csv/sprint_lap_chart.csv", index=False)
    print("----- CSV file created for sprint lap chart -----")
    return

def create_race_history_chart():
    data = parse_race_history_chart("data/race_history_chart.pdf")
    data.to_csv("csv/race_history_chart.csv", index=False)
    print("----- CSV file created for race history chart -----")
    return

def create_race_classification():
    data = parse_race_final_classification("data/race_classification.pdf")
    data.to_csv("csv/race_classification.csv", index=False)
    print("----- CSV file created for race classification -----")
    return

def create_race_lap_chart():
    data = parse_race_lap_chart("data/race_lap_chart.pdf")
    data.to_csv("csv/race_lap_chart.csv", index=False)
    print("----- CSV file created for race lap chart -----")
    return

def create_race_pit_stops():
    data = parse_race_pit_stop("data/race_pit_stops.pdf")
    data.to_csv("csv/race_pit_stops.csv", index=False)
    print("----- CSV file created for race pit stops -----")
    return

def create_drivers_championship():
    data = parse_driver_championship("data/drivers_championship.pdf")
    data.to_csv("csv/drivers_championship.csv", index=False)
    print("----- CSV file created for drivers championship -----")
    return

def create_constructors_championship():
    data = parse_constructor_championship("data/constructors_championship.pdf")
    data.to_csv("csv/constructors_championship.csv", index=False)
    print("----- CSV file created for constructors championship -----")
    return

def snake_case(s: str) -> str:
    return '_'.join(
        sub('([A-Z][a-z]+)', r' \1',
        sub('([A-Z]+)', r' \1',
        s.replace('-', ' '))).split()).lower()

def kebab_case(s: str) -> str:
  return '-'.join(
    sub(r"(\s|_|-)+"," ",
    sub(r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
    lambda mo: ' ' + mo.group(0).lower(), s)).split())


if __name__ == "__main__":
    # Get round number and circuit contry from stdin arguments
    race_name = sys.argv[1]

    # Transform race name to kebab case and snake case
    snake_race_name = snake_case(race_name)
    kebab_race_name = kebab_case(race_name)

    today = date.today()
    is_sprint = sys.argv[2] == "true"

    # Load contries.json file
    file = open("countries.json", "r")
    countries = json.load(file)

    try :
        key = snake_race_name
        # download_files(today.year, kebab_race_name, is_sprint)

        # Qualifying
        create_quali_classification()

        # Race
        create_race_history_chart()
        create_race_classification()
        create_race_lap_chart()
        create_race_pit_stops()

        # Championship
        create_drivers_championship()
        create_constructors_championship()

        if is_sprint:
            print("----- Handling sprint weekend -----")
            create_sprint_history_chart()
            create_sprint_classification()
            create_sprint_lap_chart()
    except Exception as e:
        print(e)
        exit(1)

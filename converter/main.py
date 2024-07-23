from datetime import date
from re import sub
from urllib.request import urlopen
from bs4 import BeautifulSoup
from bs4.element import Tag

import requests
from pathlib import Path
import pdfplumber
import json
import sys

from parser.parse_race_history_chart import parse_race_history_chart

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
            "History Chart"
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

        if div.name == "p" and b_tag is not None:
            for header in files_url:
                if header == b_tag.getText(strip=True):
                    current_header = header
                    break
                else:
                    current_header = ""

        classes = div.get("class")

        if classes is None or classes[0] != 'for-documents':
            continue

        if current_header == "":
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
    fn = f"data/quali_classification.pdf"

    pdf = pdfplumber.open(fn)
    page = pdf.pages[0]

    tables = page.extract_tables()

    file = Path(f"csv/quali_classification.csv")
    file.parent.mkdir(parents=True, exist_ok=True)

    # Remove 4th and 5th element of each row
    tables[0] = [row[:3] + row[5:] for row in tables[0]]

    text = ",".join(["pos", "no", "driver", "entrant", "q1", "q1_laps", "q1_time", "q2", "q2_laps", "q2_time", "q3", "q3_laps", "q3_time"]) + "\n"
    for row in tables[0]:
        row[3] = entrant_mapping.get(row[3], row[3])
        text += ",".join(row) + "\n"

    file.write_text(text)

    print("----- CSV file created for quali classification -----")
    return

def create_sprint_lap_analysis():
    fn_lap_analysis = f"data/sprint_history_chart.pdf"

    lap_analysis_options = {}

    pdf_lap_analysis = pdfplumber.open(fn_lap_analysis)

    laps = []
    lap = 1

    for page in pdf_lap_analysis.pages:
        tables = page.extract_tables()
        for table in tables:
            for j in range(len(table)):
                row = table[j]
                m = row[2].split(":")[0]
                s = row[2].split(":")[1].split(".")[0]
                ms = row[2].split(":")[1].split(".")[1]
                mmm = int(m) * 60000 + int(s) * 1000 + int(ms)
                laps.append([lap, row[0], row[2], j + 1, mmm])
            lap += 1

    file = Path(f"csv/sprint_laps_analysis.csv")
    file.parent.mkdir(parents=True, exist_ok=True)

    text = ",".join(["lap", "driver", "time", "position", "milliseconds"]) + "\n"
    for lap in laps:
        text += ",".join([str(lap[0]), lap[1], lap[2], str(lap[3]), str(lap[4])]) + "\n"

    file.write_text(text)
    print("----- CSV file created for sprint laps analysis -----")
    return

def create_sprint_result():
    fn_race_results = f"data/sprint_classification.pdf"
    fn_lap_chart = f"data/sprint_lap_chart.pdf"

    pdf_lap_chart = pdfplumber.open(fn_lap_chart)
    grid_start = [t for t in pdf_lap_chart.pages[0].extract_text().split("\n") if t.startswith("GRID")][0].split(" ")[1:]

    pdf_race_classification = pdfplumber.open(fn_race_results)
    tables = pdf_race_classification.pages[0].extract_tables()
    table = tables[0]

    text = ",".join(["no", "entrant", "grid", "position", "positionOrder", "points", "laps", "time", "milliseconds", "fastestLap", "rank", "fastestLapTime", "fastestLapSpeed"]) + "\n"
    fastest_lap = [r[11] for r in table]
    constructor_result = {}

    # Handle DNF
    for t in tables:
        if t[0][0] == "NOT CLASSIFIED":
            for row in t[1:]:
                if row[10] != "":
                    fastest_lap.append(row[10])
    # Sort the fastest lap times. The time is in the format MM:SS.mmm
    fastest_lap = sorted(fastest_lap, key=lambda x: (int(x.split(":")[0]), int(x.split(":")[1].split(".")[0]), int(x.split(":")[1].split(".")[1])))
    for i in range(len(table)):
        row = table[i]
        if row[-1] != '':
            points = int(row[-1])
        else:
            points = 0

        if i == 0:
            lap_time = row[7]
        else:
            lap_time = row[8]

        if row[5] not in constructor_result:
            constructor_result[row[5]] = points
        else:
            constructor_result[row[5]] += points

        # Convert the time to milliseconds (time format: MM:SS.mmm)
        time = row[7].split(":")
        min = int(time[0])
        sec = int(time[1].split(".")[0])
        mmm = int(time[1].split(".")[1])
        milliseconds = min * 60000 + sec * 1000 + mmm

        if row[11] in fastest_lap:
            fastest_lap_index = fastest_lap.index(row[11]) + 1
        else:
            fastest_lap_index = 0

        text += ",".join([row[1], entrant_mapping[row[5]], str(grid_start.index(row[1]) + 1), row[0], row[0], str(points), row[6], lap_time, str(milliseconds), row[12], str(fastest_lap_index), row[11], row[10]]) + "\n"

    finishers = len(table)

    # Handle DNF
    for t in tables:
        if t[0][0] == "NOT CLASSIFIED":
            table = t[1:]
            for i in range(len(table)):
                row = table[i]

                if row[-1] != '':
                    points = int(row[-1])
                else:
                    points = 0

                if row[4] not in constructor_result:
                    constructor_result[row[4]] = points
                else:
                    constructor_result[row[4]] += points

                if row[11] in fastest_lap:
                    fastest_lap_index = fastest_lap.index(row[11]) + 1
                else:
                    fastest_lap_index = 0

                text += ",".join([row[0], entrant_mapping[row[4]], str(grid_start.index(row[0]) + 1), 'R', str(finishers + i + 1), str(points), row[5], '', '', row[11], str(fastest_lap_index), row[10], row[9]]) + "\n"

    constructor_text = ",".join(["constructor", "points"]) + "\n"
    for constructor in constructor_result:
        name = entrant_mapping[constructor]
        constructor_text += f"{constructor},{constructor_result[constructor]}\n"


    driver_file = Path(f"csv/driver_sprint_result.csv")
    driver_file.parent.mkdir(parents=True, exist_ok=True)

    constructor_file = Path(f"csv/constructor_sprint_result.csv")
    constructor_file.parent.mkdir(parents=True, exist_ok=True)

    driver_file.write_text(text)
    constructor_file.write_text(constructor_text)
    print("----- CSV file created for sprint result -----")
    return

def create_race_lap_analysis():
    data = parse_race_history_chart("data/race_history_chart.pdf")
    data.to_csv("csv/laps_analysis.csv", index=False)
    print("----- CSV file created for laps analysis -----")
    return

def create_race_result():
    fn_race_results = f"data/race_classification.pdf"
    fn_lap_chart = f"data/race_lap_chart.pdf"

    pdf_lap_chart = pdfplumber.open(fn_lap_chart)
    grid_start = [t for t in pdf_lap_chart.pages[0].extract_text().split("\n") if t.startswith("GRID")][0].split(" ")[1:]

    pdf_race_classification = pdfplumber.open(fn_race_results)
    tables = pdf_race_classification.pages[0].extract_tables()
    table = tables[0]

    text = ",".join(["no", "entrant", "grid", "position", "positionOrder", "points", "laps", "time", "milliseconds", "fastestLap", "rank", "fastestLapTime", "fastestLapSpeed"]) + "\n"
    fastest_lap = [r[11] for r in table]
    constructor_result = {}

    # Handle DNF
    for t in tables:
        if t[0][0] == "NOT CLASSIFIED":
            for row in t[1:]:
                if row[10] != "":
                    fastest_lap.append(row[10])
    # Sort the fastest lap times. The time is in the format MM:SS.mmm
    fastest_lap = sorted(fastest_lap, key=lambda x: (int(x.split(":")[0]), int(x.split(":")[1].split(".")[0]), int(x.split(":")[1].split(".")[1])))
    for i in range(len(table)):
        row = table[i]
        if row[-1] != '':
            points = int(row[-1])
        else:
            points = 0

        if i == 0:
            lap_time = row[7]
        else:
            lap_time = row[8]

        if row[5] not in constructor_result:
            constructor_result[row[5]] = points
        else:
            constructor_result[row[5]] += points

        if row[11] in fastest_lap:
            fastest_lap_index = fastest_lap.index(row[11]) + 1
        else:
            fastest_lap_index = 0

        # Convert the time to milliseconds (time format: hh:MM:SS.mmm)
        time = row[7].split(":")
        milliseconds = int(time[0]) * 3600000 + int(time[1]) * 60000 + int(time[2].split(".")[0]) * 1000 + int(time[2].split(".")[1])

        text += ",".join([row[1], entrant_mapping[row[5]], str(grid_start.index(row[1]) + 1), row[0], row[0], str(points), row[6], lap_time, str(milliseconds), row[12], str(fastest_lap_index), row[11], row[10]]) + "\n"

    finishers = len(table)

    # Handle DNF
    for t in tables:
        if t[0][0] == "NOT CLASSIFIED":
            table = t[1:]
            for i in range(len(table)):
                row = table[i]

                if row[-1] != '':
                    points = int(row[-1])
                else:
                    points = 0

                if row[4] not in constructor_result:
                    constructor_result[row[4]] = points
                else:
                    constructor_result[row[4]] += points

                if row[11] in fastest_lap:
                    fastest_lap_index = fastest_lap.index(row[11]) + 1
                else:
                    fastest_lap_index = 0

                text += ",".join([row[0], entrant_mapping[row[4]], str(grid_start.index(row[0]) + 1), 'R', str(finishers + i + 1), str(points), row[5], '', '', row[11], str(fastest_lap_index), row[10], row[9]]) + "\n"

    constructor_text = ",".join(["constructor", "points"]) + "\n"
    for constructor in constructor_result:
        name = entrant_mapping[constructor]
        constructor_text += f"{name},{constructor_result[constructor]}\n"


    driver_file = Path(f"csv/driver_race_result.csv")
    driver_file.parent.mkdir(parents=True, exist_ok=True)

    constructor_file = Path(f"csv/constructor_race_result.csv")
    constructor_file.parent.mkdir(parents=True, exist_ok=True)

    driver_file.write_text(text)
    constructor_file.write_text(constructor_text)
    print("----- CSV file created for race result -----")
    return

def create_drivers_championship():
    fn = f"data/drivers_championship.pdf"

    pdf = pdfplumber.open(fn)

    text = ",".join(["driver", "points", "position", "wins"]) + "\n"

    for page in range(len(pdf.pages)):
        table = pdf.pages[page].extract_tables()[0]

        for row in table:
            wins = len([r for r in row[3:] if len(r.split("\n")) == 2 and (r.split("\n")[1] == "1" or r.split("\n")[1] == "1F")])
            text += ",".join([row[1], row[2], row[0], str(wins)]) + "\n"


    file = Path(f"csv/drivers_championship.csv")
    file.parent.mkdir(parents=True, exist_ok=True)

    file.write_text(text)
    print("----- CSV file created for drivers championship -----")
    return

def create_constructors_championship():
    fn = f"data/constructors_championship.pdf"

    pdf = pdfplumber.open(fn)

    text = ",".join(["constructor", "points", "position", "wins"]) + "\n"

    for page in range(len(pdf.pages)):
        table = pdf.pages[page].extract_tables()[0]

        for row in table:
            wins = len([r for r in row[3:] if len(r.split("\n")) >= 2 and (r.split("\n")[len(r.split("\n")) - 2] == "1" or r.split("\n")[len(r.split("\n")) - 2] == "F 1")])
            constructor = " ".join(row[1].split("\n"))
            name = entrant_mapping[constructor]
            text += ",".join([name, row[2], row[0], str(wins)]) + "\n"


    file = Path(f"csv/constructors_championship.csv")
    file.parent.mkdir(parents=True, exist_ok=True)

    file.write_text(text)
    print("----- CSV file created for constructors championship -----")
    return

def create_pit_stops():
    fn = f"data/race_pit_stops.pdf"

    pdf = pdfplumber.open(fn)

    text = ",".join(["no", "driver", "stop", "lap", "time", "duration", "milliseconds"]) + "\n"

    for page in range(len(pdf.pages)):
        table = pdf.pages[page].extract_tables()[0]

        for row in table:
            if len(row[6].split(":")) == 2:
                m = int(row[6].split(":")[0])
                s = int(row[6].split(":")[1].split(".")[0])
                mmm = int(row[6].split(":")[1].split(".")[1])
            else:
                m = 0
                s = int(row[6].split(":")[0].split(".")[0])
                mmm = int(row[6].split(":")[0].split(".")[1])
            milliseconds = m * 60000 + s * 1000 + mmm
            text += ",".join([row[0], row[1], row[5], row[3], row[4], row[6], str(milliseconds)]) + "\n"

    file = Path(f"csv/race_pit_stops.csv")
    file.parent.mkdir(parents=True, exist_ok=True)

    file.write_text(text)
    print("----- CSV file created for pit stops -----")
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
        download_files(today.year, kebab_race_name, is_sprint)

        create_quali_classification()
        create_race_lap_analysis()
        create_race_result()
        create_drivers_championship()
        create_constructors_championship()
        create_pit_stops()

        if is_sprint:
            print("----- Handling sprint weekend -----")
            create_sprint_lap_analysis()
            create_sprint_result()
    except Exception as e:
        print(e)
        exit(1)

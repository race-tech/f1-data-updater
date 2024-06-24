from datetime import date

import requests
from pathlib import Path
import pdfplumber
import json
import sys

endpoint = "https://www.fia.com/sites/default/files/"

files = {
    "quali_classification": "f1_q0_timing_qualifyingsessionprovisionalclassification_v01",
    "race_analysis": "f1_r0_timing_racelapanalysis_v01",
    "race_lap_chart": "f1_r0_timing_racelapchart_v01",
    "race_classification": "f1_r0_timing_raceprovisionalclassification_v01",
}

def download_files(year: int, round: int, country: str) -> str:
    # Format the key to the following format:
    # year_round_country
    # Note: the round is a 2 digit number
    key = f"{year}_{round:02d}_{country}"

    # Download the files
    for file in files:
        partial_url = endpoint + key + "_" + files[file]
        complete_url = partial_url + ".pdf"

        # Get the file
        resp = requests.get(complete_url)
        i = 1
        while resp.status_code != 200 and i < 10:
            print(f"Error: {resp.status_code} for {complete_url}")
            complete_url = partial_url + f"_{i}" + ".pdf"
            resp = requests.get(complete_url)
            i += 1

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
    print("----- Files downloaded -----")
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

    text = ",".join(["pos", "no", "driver", "entrant", "q1", "laps", "%", "time", "q2", "laps", "time", "q3", "laps", "time"]) + "\n"
    for row in tables[0]:
        text += ",".join(row) + "\n"

    file.write_text(text)

    print("----- CSV file created for quali classification -----")
    return

def convert_race_lap_analysis(key: str, year: int, round: int):
    fn_lap_analysis = f"data/{key}_race_analysis.pdf"
    fn_lap_chart = f"data/{key}_race_lap_chart.pdf"

    lap_analysis_options = {
        "intersection_x_tolerance": 10,
        "horizontal_strategy": "text",
        "intersection_y_tolerance": 25,
    }

    pdf_lap_analysis = pdfplumber.open(fn_lap_analysis)
    pdf_lap_chart = pdfplumber.open(fn_lap_chart)

    # This is a dict of list containing the lap times for each driver
    lap_analysis = {}
    lap_chart = []

    for p in range(len(pdf_lap_chart.pages)):
        text = pdf_lap_chart.pages[p].extract_text().split("\n")
        text = [t for t in text if t.startswith("LAP")]

        for lap in text:
            lap = lap.split(" ")[2:]
            lap_chart.append(lap)

    for p in range(len(pdf_lap_analysis.pages)):
        page = pdf_lap_analysis.pages[p]
        tables = page.extract_tables(lap_analysis_options)
        table = tables[0]
        table = table[4:]

        _drivers = table[0][0]
        _drivers = _drivers.split(" ")
        drivers = []
        for i in range(0, len(_drivers), 3):
            drivers.append([_drivers[i], _drivers[i + 1] + " " + _drivers[i + 2]])

        table = table[4:]

        for row in table:
            not_empty = [r for r in row if r != '']
            if len(not_empty) == 0:
                # Handle the case where the row is empty
                continue

            for driver in range(len(drivers)):
                r = row[driver * 7 + driver:driver * 7 + 7 + driver]

                if not drivers[driver][0] in lap_analysis:
                    lap_analysis[drivers[driver][0]] = {}

                if r[0] != '' and r[0] != None:
                    lap_analysis[drivers[driver][0]][r[0]] = r[2]
                if r[4] != '' and r[4] != None:
                    lap_analysis[drivers[driver][0]][r[4]] = r[6]

        for driver in lap_analysis:
            if not isinstance(lap_analysis[driver], dict):
                continue

            lap_number = list(lap_analysis[driver].keys())
            lap_analysis[driver] = [(lap_analysis[driver][str(lap)], lap_chart[lap - 1].index(driver) + 1) for lap in range(1, len(lap_number) + 1)]

    file = Path(f"csv/{year}_{round}_laps_analysis.csv")
    file.parent.mkdir(parents=True, exist_ok=True)

    text = ",".join(["lap", "driver", "time", "position"]) + "\n"
    for driver in lap_analysis:
        for i in range(len(lap_analysis[driver])):
            lap = lap_analysis[driver][i]
            text += f"{i + 1},{driver},{lap[0]},{lap[1]}\n"

    file.write_text(text)
    print("----- CSV file created for laps analysis -----")
    return

def create_race_result(key: str, year: int, round: int):
    fn_race_results = f"data/{key}_race_classification.pdf"
    fn_lap_chart = f"data/{key}_race_lap_chart.pdf"

    pdf_lap_chart = pdfplumber.open(fn_lap_chart)
    grid_start = [t for t in pdf_lap_chart.pages[0].extract_text().split("\n") if t.startswith("GRID")][0].split(" ")[1:]

    pdf_race_classification = pdfplumber.open(fn_race_results)
    tables = pdf_race_classification.pages[0].extract_tables()
    table = tables[0]

    text = ",".join(["no", "grid", "position", "positionOrder", "points", "laps", "time", "fastestLap", "rank", "fastestLapTime", "fastestLapSpeed"]) + "\n"
    fastest_lap = [r[11] for r in table]

    # Handle DNF
    for t in tables:
        if t[0][0] == "NOT CLASSIFIED":
            for row in t[1:]:
                fastest_lap.append(row[10])
    # Sort the fastest lap times. The time is in the format MM:SS.mmm
    fastest_lap = sorted(fastest_lap, key=lambda x: (int(x.split(":")[0]), int(x.split(":")[1].split(".")[0]), int(x.split(":")[1].split(".")[1])))
    for i in range(len(table)):
        row = table[i]
        if row[-1] != '':
            points = row[-1]
        else:
            points = 0

        if i == 0:
            lap_time = row[7]
        else:
            lap_time = row[8]

        text += ",".join([row[1], str(grid_start.index(row[1]) + 1), row[0], row[0], str(points), row[6], lap_time, row[12], str(fastest_lap.index(row[11]) + 1), row[11], row[10]]) + "\n"

    finishers = len(table)

    # Handle DNF
    for t in tables:
        if t[0][0] == "NOT CLASSIFIED":
            table = t[1:]
            for i in range(len(table)):
                row = table[i]

                if row[-1] != '':
                    points = row[-1]
                else:
                    points = 0

                text += ",".join([row[0], str(grid_start.index(row[0]) + 1), '', str(finishers + i + 1), str(points), row[5], '', row[11], str(fastest_lap.index(row[10]) + 1), row[10], row[9]]) + "\n"


    file = Path(f"csv/{year}_{round}_race_result.csv")
    file.parent.mkdir(parents=True, exist_ok=True)

    file.write_text(text)
    print("----- CSV file created for race result -----")
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
        convert_race_lap_analysis(key, today.year, round)
        create_race_result(key, today.year, round)
    except Exception as e:
        print(e)
        exit(1)

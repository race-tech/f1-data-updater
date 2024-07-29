# -*- coding: utf-8 -*-
import os
import pickle

import fitz
import pandas as pd


def parse_constructor_championship_page(page: fitz.Page) -> pd.DataFrame:
    """Get the table from a given page in "Constructors' Championship" PDF

    :param page: A `fitz.Page` object
    :return: A dataframe of [pos, entrant, total, wins]
    """

    # Get the position of "ENTRANT" the table is located beneath it
    t = page.search_for("ENTRANT")[0].y0

    # Page width and height
    w, h = page.bound()[2], page.bound()[3]

    df = page.find_tables(clip=fitz.Rect(0, t, w, h))[0].to_pandas()
    df.columns = ["pos"] + [c.split("-")[1].lower() for c in df.columns[1:]]  # Clean the column names
    df['wins'] = [count_wins(row) for row in df.iloc[:, 3:].values]
    df['entrant'] = df['entrant'].str.replace("\n", " ")

    return df[["pos", "entrant", "total", "wins"]]


def parse_constructor_championship(file: str | os.PathLike[str]) -> pd.DataFrame:
    """
    Parse "Constructors' Championship" PDF

    :param file: Path to PDF file
    :return: The output dataframe will be [pos, entrant, total, wins]
    """
    # Get page width and height
    doc = fitz.open(file)
    page = doc[0]
    global W
    W = page.bound()[2]

    # Parse all pages
    tables = []
    for page in doc:
        tables.append(parse_constructor_championship_page(page))
    df = pd.concat(tables, ignore_index=True)

    return df

# Count the number of wins for a given row
def count_wins(row):
    result = 0
    for i in range(len(row)):
        if len(row[i].split("\n")) < 2:
            continue
        else:
            pos = row[i].split("\n")[1]
            if pos == "1" or pos == "1F":
                result += 1
            else:
                continue
    return result

if __name__ == '__main__':
    pass

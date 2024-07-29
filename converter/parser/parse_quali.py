# -*- coding: utf-8 -*-
import os

import fitz
import pandas as pd


def parse_quali_final_classification(file: str | os.PathLike) -> pd.DataFrame:
    """Parse "Qualifying Session Final Classification" PDF"""
    # Find the page with "Qualifying Session Final Classification"
    doc = fitz.open(file)
    found = None
    page = None
    for i in range(len(doc)):
        page = doc[i]
        found = page.search_for('Qualifying Session Final Classification')

        if len(found) == 0:
            found = page.search_for('Qualifying Session Provisional Classification')

        if len(found) > 0:
            break
    if found is None or len(found) == 0:
        raise ValueError(f'not able to find quali. result in `{file}`')

    if page is None:
        raise ValueError(f'not able to find quali. result in `{file}`')

    # Width and height of the page
    w, h = page.bound()[2], page.bound()[3]

    # y-position of "Qualifying Final Classification" or "Qualifying Session Provisional Classification"
    y = found[0].y1

    # y-position of "NOT CLASSIFIED - " or "POLE POSITION LAP"
    not_classified = page.search_for('NOT CLASSIFIED - ')
    b = None
    if len(not_classified) > 0:
        b = not_classified[0].y0
    elif len(page.search_for('POLE POSITION LAP')) > 0:
        b = page.search_for('POLE POSITION LAP')[0].y0
    elif len(page.search_for('FASTEST LAP')) > 0:
        b = page.search_for('FASTEST LAP')[0].y0
    elif len(page.search_for('Formula One World Championship')[0]) > 0:
        b = page.search_for('Formula One World Championship')[0].y0
    else:
        raise ValueError(f'not able to find the bottom of quali. result in `{file}`')
    if b is None:
        raise ValueError(f'not able to find the bottom of quali. result in `{file}`')

    # Table bounding box
    bbox = fitz.Rect(0, y, w, b)

    # Dist. between "NAT" and "ENTRANT"
    nat = page.search_for('NAT')[0]
    entrant = page.search_for('ENTRANT')[0]
    snap_x_tolerance = (entrant.x0 - nat.x1) * 1.2  # 20% buffer

    # Parse
    df = page.find_tables(clip=bbox, snap_x_tolerance=snap_x_tolerance)[0].to_pandas()
    first_row = [format_col(c) for c in df.columns]
    # Insert the new column names
    df.columns = ['_', 'no', 'driver', 'nat', 'entrant', 'q1', 'q1_laps', 'q1_time', 'q2',
                          'q2_laps', 'q2_time', 'q3', 'q3_laps', 'q3_time']
    df = pd.concat([pd.DataFrame([first_row], columns=df.columns), df], ignore_index=True)
    df.drop(columns=['_', 'nat'], inplace=True)
    df = df[df['no'] != '']
    return df

# Format the first line elements
def format_col(c: str) -> str:
    if len(c.split("-")) > 1:
        return c.split("-")[1]
    return c

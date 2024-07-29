# -*- coding: utf-8 -*-
import os
import pickle

import fitz
import pandas as pd


def parse_race_pit_stop(file: str | os.PathLike[str]) -> pd.DataFrame:
    """Parse the table from "Pit Stop Summary" PDF

    :param file: Path to PDF file
    :return: A dataframe of [driver No., lap No., local time of the stop, pit stop No., duration]
    """

    doc = fitz.open(file)
    page = doc[0]
    # TODO: definitely have PDFs containing multiple pages

    # Get the position of the table
    t = page.search_for('DRIVER')[0].y0      # "DRIVER" gives the top of the table
    w, h = page.bound()[2], page.bound()[3]  # Page width and height
    bbox = fitz.Rect(0, t, w, h)

    # Parse
    df = page.find_tables(clip=bbox, strategy='lines')[0].to_pandas()

    # Clean up the table
    df.dropna(subset=['NO'], inplace=True)  # Drop empty rows, if any
    df = df[df['NO'] != '']
    df = df[['NO', 'LAP', 'TIME OF DAY', 'STOP', 'DURATION']].reset_index(drop=True)
    df.rename(columns={
        'NO': 'driver_no',
        'LAP': 'lap',
        'TIME OF DAY': 'local_time',
        'STOP': 'no',
        'DURATION': 'duration'
    }, inplace=True)
    return df

if __name__ == '__main__':
    pass

# -*- coding: utf-8 -*-
import os

import fitz
import pandas as pd


def parse_race_final_classification_page(file: str | os.PathLike) -> pd.DataFrame:
    """Parse "Race Final Classification" PDF

    :param file: Path to PDF file
    :return: The output dataframe will be [driver No., laps completed, total time,
                                           finishing position, finishing status, fastest lap time,
                                           fastest lap speed, fastest lap No., points]
    """
    # Find the page with "Race Final Classification"
    doc = fitz.open(file)
    for i in range(len(doc)):
        page = doc[i]
        found = page.search_for('Race Final Classification')
        if len(found) > 0:
            break
        elif len(page.search_for('Race Provisional Classification')) > 0:
            found = page.search_for('Race Provisional Classification')
            break

    # Width and height of the page
    w, _ = page.bound()[2], page.bound()[3]

    # Position of "Race Final Classification"
    y = found[0].y1

    # Position of "FASTEST LAP"
    b = page.search_for('FASTEST LAP')[0].y0

    # Table bounding box
    bbox = fitz.Rect(0, y, w, b)

    # Positions of table headers/column names
    pos = {}
    for col in ['NO', 'DRIVER', 'NAT', 'ENTRANT', 'LAPS', 'TIME', 'GAP', 'INT', 'KM/H', 'FASTEST',
                'ON', 'PTS']:
        pos[col] = {
            'left': page.search_for(col, clip=bbox)[0].x0,
            'right': page.search_for(col, clip=bbox)[0].x1
        }

    # Lines separating the columns
    aux_lines = [
        pos['NO']['left'],
        (pos['NO']['right'] + pos['DRIVER']['left']) / 2,
        pos['NAT']['left'],
        pos['NAT']['right'],
        pos['LAPS']['left'],
        pos['LAPS']['right'],
        (pos['TIME']['right'] + pos['GAP']['left']) / 2,
        (pos['GAP']['right'] + pos['INT']['left']) / 2,
        (pos['INT']['right'] + pos['KM/H']['left']) / 2,
        pos['FASTEST']['left'],
        pos['FASTEST']['right'],
        pos['PTS']['left'],
        pos['PTS']['right']
    ]

    # Find the table below "Race Final Classification"
    df = page.find_tables(
        clip=fitz.Rect(pos['NO']['left'], y, w, b),
        strategy='lines',
        vertical_lines=aux_lines,
        snap_x_tolerance=pos['ON']['left'] - pos['FASTEST']['right']
    )[0].to_pandas()
    df = df[df['NO'] != '']  # May get some empty rows at the bottom

    # Clean a bit
    df.drop(columns=['DRIVER', 'NAT', 'ENTRANT', 'INT', 'KM/H'], inplace=True)
    df.columns = ['driver_no', 'laps', 'time', 'gap', 'fastest', 'on', 'points'] # [NO,LAPS,TIME,GAP,FASTEST,ON,PTS]
    return df


if __name__ == '__main__':
    pass
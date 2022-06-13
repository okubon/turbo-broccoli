import xml.etree.ElementTree as ET
from snorkel.labeling import labeling_function
import pandas as pd
import re
from collections import Counter


def load_data(path):
    tree = ET.parse(path)
    root = tree.getroot()
    return root


def clean_list(input):
    output = []
    for item in input:
        l = len(item)
        new_item = item[:l-1]
        output.append(new_item)
    return output


@labeling_function()
def beitrag(txt):
    # find all: "name (ort) (partei):" or "name (partei):" or "name (partei/partei):"
    list = re.findall("([a-zA-ZÄäÜüÖö]+\s\([^)]*\)\s\([^)]*\):|[a-zA-ZÄäÜüÖö]+\s\([^)]*\):)", txt)
    list = clean_list(list)
    return list

def main():
    path = './testdaten/10001.xml'
    root = load_data(path)

    # get content from xml file
    wahlperiode = root[0].text
    doukentenart = root[1].text
    nr = root[2].text
    datum = root[3].text
    titel = root[4].text
    text = root[5].text

    # get count of beiträge
    results = beitrag(text)
    counts = Counter(results)

    df = pd.DataFrame.from_dict(counts, orient = 'index').reset_index()
    print(df)


main()
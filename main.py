import xml.etree.ElementTree as ET
from snorkel.labeling import labeling_function
import pandas as pd
import re


def load_data(path):
    tree = ET.parse(path)
    root = tree.getroot()
    return root

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


    # crate label functions
    @labeling_function()
    def beitrag(txt):
        # find all: "name (ort) (partei):" or "name (partei):" or "name (partei/partei):"
        list = re.findall("([a-zA-ZÄäÜüÖö]+\s\([^)]*\)\s\([^)]*\):|[a-zA-ZÄäÜüÖö]+\s\([^)]*\):)", txt)
        return list

    # empty df to store results from label function
    df = pd.DataFrame()

    list = beitrag(text)
    count = list.count(value)

    print(count)


main()
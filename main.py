import xml.etree.ElementTree as ET
from snorkel.labeling import labeling_function
import pandas as pd
import re
from collections import Counter

def load_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    return root

def clean_items(input):
    '''
    Cleans the item in a list from colons.
    Example: "Stratmann (GRÜNE):" -> "Stratmann (GRÜNE)"
    '''
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
    list = clean_items(list)
    return list

def main(path):
    root = load_xml(path)

    # get content from xml file
    wahlperiode = root[0].text
    dokumentenart = root[1].text
    nr = root[2].text
    datum = root[3].text
    titel = root[4].text
    text = root[5].text

    # get count of beiträge
    results = beitrag(text)
    counts = Counter(results)

    # create results in df
    df = pd.DataFrame.from_dict(counts, orient = 'index').reset_index()
    df = df.rename(columns={'index':'Name', 0:'Anzahl Beiträge'})
    print(df)



path = './testdaten/10001.xml'
main(path)
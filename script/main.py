import xml.etree.ElementTree as ET
from snorkel.labeling import labeling_function
import nltk.data
import pandas as pd
import re
from collections import Counter
import os

def load_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    return root

def clean_rb_item(input):
    '''
    Cleans the item in a list from colons.
    Example: "Stratmann (GRÜNE):" -> "Stratmann (GRÜNE)"
    '''
    l = len(input)
    output = input[:l-1]
    return output

def clean_ko_item(input):
    # Cleans the item in a list from colons.
    l = len(input)
    input = input[:l-1]

    # Splits after '— '
    if '— ' in input:
        output = input.split(sep='— ', maxsplit=1)[1]
    else:
        output = input

    if output[0] == '—':
        output = output[1:]

    return output

def typeofspeech(str, rb_regex, ko_regex):
    if re.match(rb_regex, str):
        typeofspeech = 'rb'
    elif re.match(ko_regex, str):
        typeofspeech = 'ko'
    else:
        typeofspeech = "Null"

    return typeofspeech

@labeling_function()
def get_RB(rb_regex, sentence):
    '''
    Name (Partei):
    Name (Partei/Partei):
    Name (Stadt):
    Name (Stadt) (Partei):
    Name (Stadt) (Partei/Partei):
    '''
    list = re.findall(rb_regex, sentence)

    return list[0]

@labeling_function()
def get_KO(ko_regex, sentence):
    '''
    (Conradi [SPD]: Und wer soll das bezahlen?)
    (Dr. Dregger [CDU/CSU]: Sehr gut!)
    (Kleinert [Marburg] [GRÜNE]: Vor allemgerechter!)
    (Beifall bei der CDU/CSU und der FDP — Dr. Apel [SPD]: Es ist doch völlig unrichtig, was Sie sagen!)
    (Beifall bei der SPD - Zuruf des Abg. Dr. Waigel [CDU/CSU])

    Hauser [Krefeld]\n[CDU/CSU]

    (Name [Partei]: Text)
    (Name [Partei/Partei]: Text)
    (Text — Name [Partei]: Text)
    '''
    list = re.findall(ko_regex, sentence)
    return list[0]

def get_the_juice_stuff(file, rb_ID):
    # get meta data and content from xml file
    WAHLPERIODE = file[0].text
    DOKUMENTENART = file[1].text
    NR = file[2].text
    DATUM = file[3].text
    TITEL = file[4].text
    TEXT = file[5].text

    # split the text in single sentences
    text = split_text(TEXT)

    # empty dicts to store the results
    rb_dict = {}
    ko_dict = {}

    # regex for the different typ of speeches
    rb_regex = "([a-zA-ZÄäÜüÖö]+\s\([^)]*\)\s\([^)]*\):|[a-zA-ZÄäÜüÖö]+\s\([^)]*\):)"
    ko_regex = "[a-zA-Z]+.*\[.*\]:"

    # iteration through sentences
    for sentence in text:
        type = typeofspeech(sentence, rb_regex, ko_regex)
        if type == 'rb':
            rb_ID += 1
            rb_list = re.findall(rb_regex, sentence)
            rb_dict[str(rb_ID)] = clean_rb_item(rb_list[0])
        elif type == 'ko':
            ko_list = re.findall(ko_regex, sentence)
            ko_dict[str(rb_ID)] = clean_ko_item(ko_list[0])
    
    # create rb df
    rb_df = pd.DataFrame.from_dict(rb_dict, orient = 'index').reset_index()
    rb_df = rb_df.rename(columns={'index':'RB_ID', 0:'RB_Name'})
    # add the rest of imformation to df
    rb_df['WAHLPERIODE'] = WAHLPERIODE
    rb_df['NR'] = NR
    rb_df['DATUM'] = DATUM

    # create ko df
    ko_df = pd.DataFrame.from_dict(ko_dict, orient = 'index').reset_index()
    ko_df = ko_df.rename(columns={'index':'RB_ID', 0:'KO_Name'})

    return rb_df, ko_df, rb_ID
    

def export_rb(df):
    df.to_csv(r'script/RB.csv', index = False)
    return

def export_ko(df):
    df.to_csv(r'script/KO.csv', index = False)
    return

def split_text(text):
    '''Splits text into single sentences when \n occurs'''
    split_text = text.split("\n")
    return split_text

def main(dir, rb_ID):
    # empty dfs to store results for RB and KO
    RB_df = pd.DataFrame()
    KO_df = pd.DataFrame()

 

    # iteration through files
    for filename in os.listdir(dir):
        filepath = os.path.join(dir, filename)
        file = load_xml(filepath)

        results = get_the_juice_stuff(file, rb_ID)

        RB_df = pd.concat([RB_df,results[0]])
        KO_df = pd.concat([KO_df,results[1]])

        rb_ID = results[2]
 
    # export df to csv
    export_rb(RB_df)
    export_ko(KO_df)


rb_ID = 0
main('testdaten', rb_ID)
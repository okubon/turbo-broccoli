from operator import contains
import xml.etree.ElementTree as ET
from snorkel.labeling import labeling_function
import nltk.data
import pandas as pd
import re
from collections import Counter
import os
import xml.etree.ElementTree as ETree
import pandas

def load_xml(path):
    ''''''
    tree = ET.parse(path)
    root = tree.getroot()
    return root

def get_file(filename):
    filepath = os.path.join(dir, filename)
    file = load_xml(filepath)
    return file

def split_text(text):
    '''Splits text into single sentences when \n occurs'''
    split_text = text.split("\n")
    return split_text

def create_RB_regex():
    '''
    regex for the different typ of RB

    # base
    catch all RB with () in it. It's the base and finds the most RB

    # title
    finds stuff like: "Dr. Schröder,  Bundesminister des Innern:" 

    # funktion
    finds stuff like: "Schäfer, Staatsminister im Auswärtigen Amt:"

    # ralterspraesident
    finds stuff like: "Alterspräsident Labe:"
    
    '''
    dict = {
        'base': "([a-zA-ZÄäÜüÖöß]+\s\([^)]*\)\s\([^)]*\):|[a-zA-ZÄäÜüÖöß]+\s\([^)]*\).*:)",
        'title': "[a-zA-Z]+\..*[a-zA-Z]+.*:",   
        'alterspraesident': "Alterspräsident [a-zA-Z]+:"
    }
    # 'funktion': "[A-Z]+.*,.*:",
    #'title': "[a-zA-Z]+\..*[a-zA-Z]+.*:",   
    #'alterspraesident': "Alterspräsident [a-zA-Z]+:"
    return dict

def create_KO_regex():
    '''
    regex for the different typ of KO
    '''
    dict = {
        "base": "[a-zA-Z]+.*\[.*\]:"
    }


    return dict

def typeofspeech(str, rb_regex, ko_regex):
    # check if its RB
    for key in rb_regex.keys():
        if re.match(rb_regex[key], str):
            type = 'rb'
            regex = rb_regex[key]
            break
        else:
            for key in ko_regex.keys():
                if re.match(ko_regex[key], str):
                    type = 'ko'
                    regex = ko_regex[key]
                    break
                else:
                    type = "Null"
                    regex = "Null"
    return type, regex

def clean_rb_df(df):
    # key words in rb to skip
    discard = ["Drucksache",  
                "Geschäftsordnung", 
                "Tagesordnungspunkt",
                "Verordnung",
                "Ausschuss",
                "abschätzung",
                "Schriftlicher",
                "§",
                "Ratsdok",
                "Ergänzung",
                "btr.",
                "Fortsetzung",
                "vergessen",
                "Fragen",
                "Drittens",
                "Zweitens",
                "Haushaltsführung",
                "Erstens",
                "z. B.",
                "Elftens",
                "Viertens",
                "Fünftens",
                "Sechstens",
                "Siebtens",
                "Achtens",
                "Neuntens",
                "Zehntens",
                "Frieden",
                "Indessen",
                "Mensch",
                "Bundesregierung",
                "Februar",
                "Er",
                "Sie",
                "wir",
                "Abs.",
                "Reform",
                "Alle",
                "der",
                "die",
                "das",
                "Ich",
                "Du",
                "Frage",
                "F.D.P.",
                "Was",
                "Warum",
                "Wie",
                "Beispiel"]

    # check if sentence is needed
    for item in discard:
        df = df[~df.RB_Name.str.contains('|'.join(discard))]
    return df

def clean_rb_item(input):
    step1 = input.split(':')
    step2 = step1[0].split(',')
    step3 = step2[0].split(' .')
    step4 = step3[0].split('   ')
    step5 = step4[0].split(' 	')
    step6 = step5[0].split('	')
    step7 = step6[0].split(' 	 ')
    step8 = re.split(r'\d', step7[0], maxsplit=1)
    return step8[0]

def clean_ko_item(input):
    # Cleans the item in a list from colons.
    l = len(input)
    input = input[:l-1]

    # Splits after '— '
    if '— ' in input:
        input = input.split(sep='— ', maxsplit=1)[1]

    if input[0] == '—':
        input = input[1:]

    if ':' in input:
        input = input.split(sep=':', maxsplit=1)[1]

    if 'Abg.' in input:
        input = input.split(sep='Abg.', maxsplit=1)[1]
    
    return input

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

    # load regex variations
    rb_regex = create_RB_regex()
    ko_regex = create_KO_regex()

    # iteration through sentences
    for sentence in text:
        type = typeofspeech(sentence,rb_regex,ko_regex)[0]
        regex = typeofspeech(sentence,rb_regex,ko_regex)[1]

        if type == 'rb':
            rb_ID += 1
            rb_list = re.findall(regex, sentence)
            rb_item = clean_rb_item(rb_list[0])
            rb_dict[str(rb_ID)] = rb_item
            break
        elif type == 'ko':
            ko_list = re.findall(regex, sentence)
            ko_dict[str(rb_ID)] = clean_ko_item(ko_list[0])
            break
    
    # create rb df
    rb_df = pd.DataFrame.from_dict(rb_dict, orient = 'index').reset_index()
    rb_df = rb_df.rename(columns={'index':'RB_ID', 0:'RB_Name'})
    # add the rest of imformation to df
    rb_df['WAHLPERIODE'] = WAHLPERIODE
    rb_df['NR'] = NR
    rb_df['DATUM'] = DATUM
    #rb_df = clean_rb_df(rb_df)

    # create ko df
    ko_df = pd.DataFrame.from_dict(ko_dict, orient = 'index').reset_index()
    ko_df = ko_df.rename(columns={'index':'RB_ID', 0:'KO_Name'})

    return rb_df, ko_df, rb_ID
    
def export_results(RB_df, KO_df):
    RB_df.to_csv(r'script/RB.csv',encoding='utf-8-sig', index = False)
    KO_df.to_csv(r'script/KO.csv',encoding='utf-8-sig', index = False)
    return

def main(dir, rb_ID, filenumber):
    # empty dfs to store results for RB and KO
    RB_df = pd.DataFrame()
    KO_df = pd.DataFrame()

    # iteration through files
    for filename in os.listdir(dir):
        file = get_file(filename)
        filenumber += 1

        results = get_the_juice_stuff(file, rb_ID)

        RB_df = pd.concat([RB_df,results[0]])
        KO_df = pd.concat([KO_df,results[1]])

        RB_df = clean_rb_df(RB_df)

        rb_ID = results[2]
        print(f'filenumber = {filenumber}')
 
    # export to csv
    export_results(RB_df, KO_df)

# Global vars
rb_ID = 0
filenumber = 0
dir = 'Daten_alle_WP'

main(dir, rb_ID, filenumber)
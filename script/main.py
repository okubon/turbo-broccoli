import xml.etree.ElementTree as ET
import pandas as pd
import re
import os
import time
import glob

def load_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    return root

def get_file(filename):
    #filepath = os.path.join(dir, filename)
    file = load_xml(filename)
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
    
    '''#         ([a-zA-ZÄäÜüÖö]+\s\([^)]*\)\s\([^)]*\):|[a-zA-ZÄäÜüÖö]+\s\([^)]*\):)
    dict = {
        'base': "([a-zA-ZÄäÜüÖöß]+\s\([^)]*\)\s\([^)]*\):|[a-zA-ZÄäÜüÖöß]+\s\([^)]*\).*?:)"
    }
    ## Weitere regexfunktionen
    # 'base': "([a-zA-ZÄäÜüÖöß]+\s\([^)]*\)\s\([^)]*\):|[a-zA-ZÄäÜüÖöß]+\s\([^)]*\).*:)"
    # 'funktion': "[A-Z]+.*,.*:",
    # 'title': "Dr\..*[a-zA-ZÄäÜüÖöß]+.*:",   
    # 'alterspraesident': "Alterspräsident [a-zA-Z]+:"
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
        match = re.match(rb_regex[key], str)
        if match:
            type = 'rb'
        else:
            for key in ko_regex.keys():
                match = re.match(ko_regex[key], str)
                if match:
                    type = 'ko'
                else:
                    type = "Null"
                    match = ["Null"]
    return type, match[0]

def clean_rb_df(df):
    # key words in rb to skip
    discard = ["Drucksache",  
                "Geschäftsordnung", 
                "Tagesordnungspunkt",
                "Verordnung",
                "Ausschuss","ausschusses","schusses","ses \(",
                "gie \(",
                "Schriftlicher",
                "§",
                "Ratsdok",
                "Ergänzung",
                "btr.",
                "Fortsetzung",
                "Fragen",
                "Haushaltsführung",
                "folgenabschätzung", "abschätzung"]

    # check if sentence is needed
    for item in discard:
        df = df[~df.RB_Name.str.contains('|'.join(discard))]
    return df

def clean_rb_item(input):
    step1 = input.split(':')
    step2 = step1[0].split(',')
    step3 = step2[0].split(' . ')
    step4 = re.split(r'\d', step3[0], maxsplit=1)
    output = step4[0].strip()
    return output

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

def get_the_juice_stuff(file, rb_ID,rb_regex,ko_regex,rb_dict,ko_dict):
    # get meta data and content from xml file
    WAHLPERIODE = file[0].text
    DOKUMENTENART = file[1].text
    NR = file[2].text
    DATUM = file[3].text
    TITEL = file[4].text
    TEXT = file[5].text

    # split the text in single sentences
    text = split_text(TEXT)

    # iteration through sentences
    for sentence in text:
        check = typeofspeech(sentence,rb_regex,ko_regex)
        type = check[0]
        match = clean_rb_item(check[1])

        if type == 'rb':
            rb_ID += 1
            rb_dict[str(rb_ID)] = match
        elif type == 'ko':
            ko_dict[str(rb_ID)] = match
    
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

def export_results(RB_df, KO_df,WP):
    RB_df.to_csv(rf'output/rb/{WP}.csv',encoding='utf-8-sig', index = False)
    #KO_df.to_csv(rf'output/ko/%.csv' % WAHLPERIODE,encoding='utf-8-sig', index = False)
    return

def main(dir, rb_ID, filenumber):
    # empty dfs to store results for RB and KO
    RB_df = pd.DataFrame()
    KO_df = pd.DataFrame()

    # load regex variations
    rb_regex = create_RB_regex()
    ko_regex = create_KO_regex()

    # empty dicts to store the results
    rb_dict = {}
    ko_dict = {}

    # iteration through files
    for root, dirs, files in os.walk(dir):
        for name in files:
            t0 = time.time()
            filename =  os.path.join(root, name)
            file = get_file(filename)
            filenumber += 1

            results = get_the_juice_stuff(file, rb_ID,rb_regex,ko_regex,rb_dict,ko_dict)
            
            #Clean_rb_df = clean_rb_df()

            RB_df = pd.concat([RB_df,results[0]])
            KO_df = pd.concat([KO_df,results[1]])
            rb_ID = results[2]

            t1 = time.time()
            total = t1 - t0
            print(f'filenumber = {filenumber} - time: {total}')

            # export to csv
            WP = WAHLPERIODE = file[0].text
            export_results(RB_df, KO_df, WP)
            RB_df = RB_df.iloc[0:0]
            KO_df = KO_df.iloc[0:0]
    #
    # alle csv dateien zusammen setzen
    path = "output/rb/"

    all_files = glob.glob(os.path.join(path, "*.csv"))
    df_from_each_file = (pd.read_csv(f, sep=',') for f in all_files)
    df_merged   = pd.concat(df_from_each_file, ignore_index=True)
    df_merged.to_csv( "output/rb_merged.csv")

# Global vars
rb_ID = 0
filenumber = 0
dir = 'protokolle_wp_1-12/'

main(dir, rb_ID, filenumber)
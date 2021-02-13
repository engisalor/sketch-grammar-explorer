import pandas as pd
import numpy as np
import glob
import re

####
# this script takes word sketch frequency results and combines them for visualization
####

#### test a single file
freqs = np.load('data/ws/ws_freqs_isatypeof_Domain_Biology.npy', allow_pickle="TRUE").item()
freqs1 = [freqs["Blocks"][x]["Items"] for x in range(0, len(freqs["Blocks"]))]
temp = pd.DataFrame()
for x in range(0, len(freqs1)):
    temp = temp.append(pd.DataFrame.from_dict(freqs1[x]))

#### MAKE DATAFRAME

# merge all freqs files
filesAPI = glob.glob("data/ws/" + "*.npy")
dfAPI = pd.DataFrame()
# process individual files
for file in filesAPI:
    try:
        # load whole freqs file
        freqs = np.load(file, allow_pickle="TRUE").item()
        # get blocks from file
        freqs1 = [freqs["Blocks"][x]["Items"] for x in range(0, len(freqs["Blocks"]))]
        # create df and fill with blocks
        temp = pd.DataFrame()
        for x in range(0, len(freqs1)):
            temp = temp.append(pd.DataFrame.from_dict(freqs1[x]))
        # get query string and replace problem values
        query = str(freqs["request"]["q"])
        query = re.sub(r"=+none=+", "none", query, flags=re.IGNORECASE)
        # add columns
        temp["ws"] = re.search(r',"\.\*(.*)\.\.\.",',query).group(1)
        temp["text type"] = re.search(r'<doc \((.*)=\"',query).group(1)
        temp["value"] = re.search(r'' + temp["text type"][0] + '=(.*)\) />',query).group(1).replace('"', '')
        temp["word"] = [temp.iloc[x]["Word"][0]["n"] for x in range(0, len(temp))]
        # get relevant columns to graph
        temp = temp.filter(["ws", "text type", "value", "word", "frq", "fpm"], axis=1)
        # append to dfAPI
        dfAPI = dfAPI.append(temp, sort=False)
    except:
        print("*** problem with " + file + " ***")


# TODO some strings have double spaces within text

#### RENAME STRINGS
dfAPI.reset_index(drop=True, inplace=True)
# change specific (sub)strings
dfAPI.loc[(dfAPI["text type"] == "domains"), "text type"] = "domain" 
dfAPI.loc[(dfAPI["value"] == "Bussiness and NGOs"), "value"] = "Business/NGO" 
dfAPI.loc[(dfAPI["value"] == "Goverment"), "value"] = "Government"
dfAPI.loc[(dfAPI["value"] == "mail list"), "value"] = "mailing list" 
dfAPI.loc[(dfAPI["value"] == "EEUU"), "value"] = "United States" 
dfAPI['value'] = dfAPI['value'].str.replace('Educative','Educational')
dfAPI['value'] = dfAPI['value'].str.replace('divulgative','informational')

# make strings unique to avoid graphing conflict
# ttypes = dfAPI["text type"].unique()

# for x in ttypes:
#     dfAPI.loc[dfAPI['value'].eq('unknown') & dfAPI['text type'].eq(x), 'value'] = 'Unknown/NA ' + x
#     dfAPI.loc[dfAPI['value'].eq('===NONE===') & dfAPI['text type'].eq(x), 'value'] = 'Unknown/NA ' + x

# capitalizion 
for x in ['genre']:
    dfAPI.loc[dfAPI['text type'].eq(x), 'value'] = dfAPI.loc[dfAPI['text type'].eq(x), 'value'].str.capitalize()
for x in ['domain']:
    dfAPI.loc[dfAPI['text type'].eq(x), 'value'] = dfAPI.loc[dfAPI['text type'].eq(x), 'value'].str.title()
    dfAPI.loc[dfAPI['text type'].eq(x), 'value'] = dfAPI.loc[dfAPI['text type'].eq(x), 'value'].str.replace(' And ',' and ')
    dfAPI.loc[dfAPI['text type'].eq(x), 'value'] = dfAPI.loc[dfAPI['text type'].eq(x), 'value'].str.replace('Domain','domain')
dfAPI["text type"] = dfAPI["text type"].str.title()
dfAPI['value'] = dfAPI['value'].str.replace('/Na','/NA')
dfAPI['value'] = dfAPI['value'].str.replace('/na','/NA')

#### OTHER
# change index (for displaying in alldata table)
# dfAPI["data point"] = range(0,len(dfAPI))
# dfAPI.sort_values(by="data point")
# drop rows from unwanted text types
# drops = dfAPI[dfAPI['text type'].isin(["Author", "Title", "Keywords", "Variant", "Year", "Country"])].index
# dfAPI.drop(drops, inplace=True)

dfAPI.to_csv("data/ws_freqs.csv",index=False)



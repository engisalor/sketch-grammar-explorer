import pandas as pd
import numpy as np
import glob
import re

#### DATA COLLECTION
# read grammar file
with open("grammar.txt") as f:
    lines = [line.rstrip() for line in f]
lines = lines[lines.index("### Pilar's relations start here") :]
# get indexes of CQL lines
cqllines = [i for i, x in enumerate(lines) if "[" in x]
# make dict of indexes, gramrels & CQL
dtGRAM = {}
for i in range(0, len(cqllines)):
    rslice = reversed(lines[: cqllines[i]])
    gramrel = next((x for x in rslice if "#" in x), ["NA"])
    dtGRAM[cqllines[i]] = [gramrel, lines[cqllines[i]]]

#### DATA PREP
# merge all freqs files into dataframe
filesAPI = glob.glob("freqs/" + "*.npy")
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
        ref = int(re.findall(r"\d+", file)[0])
        # add ref
        temp["ref#"] = ref
        # add total number of concordances
        dtGRAM[ref].append(freqs["concsize"])
        # add text type
        temp["text type"] = [
            re.findall("(\w+)=", temp.iloc[x]["pfilter_list"][0])[0]
            for x in range(0, len(temp))
        ]
        # add text type value
        temp["value"] = [temp.iloc[x]["Word"][0]["n"] for x in range(0, len(temp))]
        # get relevant columns to graph
        temp = temp.filter(["freq", "fpm", "rel", "ref#", "text type", "value"], axis=1)
        # append to dfAPI
        dfAPI = dfAPI.append(temp, sort=False)
    except:
        print("*** problem with " + file + " ***")
# presort by ref#
dfAPI = dfAPI.sort_values(by=["ref#"])

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
ttypes = dfAPI["text type"].unique()

for x in ttypes:
    dfAPI.loc[dfAPI['value'].eq('unknown') & dfAPI['text type'].eq(x), 'value'] = 'Unknown/NA ' + x
    dfAPI.loc[dfAPI['value'].eq('===NONE===') & dfAPI['text type'].eq(x), 'value'] = 'Unknown/NA ' + x

# capitalizion 
for x in ['genre']:
    dfAPI.loc[dfAPI['text type'].eq(x), 'value'] = dfAPI.loc[dfAPI['text type'].eq(x), 'value'].str.capitalize()
for x in ['domain']:
    dfAPI.loc[dfAPI['text type'].eq(x), 'value'] = dfAPI.loc[dfAPI['text type'].eq(x), 'value'].str.title()
    dfAPI.loc[dfAPI['text type'].eq(x), 'value'] = dfAPI.loc[dfAPI['text type'].eq(x), 'value'].str.replace(' And ',' and ')

dfAPI["text type"] = dfAPI["text type"].str.title()
dfAPI['value'] = dfAPI['value'].str.replace('/Na','/NA')
dfAPI['value'] = dfAPI['value'].str.replace('/na','/NA')

#### STATISTICS
# comparing all relations
dfSTATSrels = pd.DataFrame.from_dict(
    dtGRAM, orient="index", columns=["relation", "cql", "concsize"]
)
dfSTATSrels.insert(0, "ref#", [i for i in dtGRAM])
dfSTATSrels["count"] = [dfAPI.loc[dfAPI["ref#"] == i]["freq"].count() for i in dtGRAM]
dfSTATSrels["count"].sum()
for y in ["freq", "fpm", "rel"]:
    dfSTATSrels[y + " min"] = [dfAPI.loc[dfAPI["ref#"] == i][y].min() for i in dtGRAM]
    dfSTATSrels[y + " max"] = [dfAPI.loc[dfAPI["ref#"] == i][y].max() for i in dtGRAM]
    dfSTATSrels[y + " mean"] = [dfAPI.loc[dfAPI["ref#"] == i][y].mean() for i in dtGRAM]
    dfSTATSrels[y + " std"] = [dfAPI.loc[dfAPI["ref#"] == i][y].std() for i in dtGRAM]
    # dfSTATSrels[y + " skew"] = [dfAPI.loc[dfAPI["ref#"] == i][y].skew() for i in dtGRAM]
    # dfSTATSrels[y + " kurt"] = [dfAPI.loc[dfAPI["ref#"] == i][y].kurt() for i in dtGRAM]

# comparing text types
dfSTATSttypes = pd.DataFrame()
dfSTATSttypes["text type"] = sorted(dfAPI["text type"].unique())
dfSTATSttypes["count"] = [
    len(dfAPI.loc[dfAPI["text type"] == x]["value"].unique())
    for x in sorted(dfAPI["text type"].unique())
]
for y in ["freq", "fpm", "rel"]:
    dfSTATSttypes[y + " min"] = [
        dfAPI.loc[dfAPI["text type"] == x][y].min()
        for x in sorted(dfAPI["text type"].unique())
    ]
    dfSTATSttypes[y + " max"] = [
        dfAPI.loc[dfAPI["text type"] == x][y].max()
        for x in sorted(dfAPI["text type"].unique())
    ]
    dfSTATSttypes[y + " mean"] = [
        dfAPI.loc[dfAPI["text type"] == x][y].mean()
        for x in sorted(dfAPI["text type"].unique())
    ]
    dfSTATSttypes[y + " std"] = [
        dfAPI.loc[dfAPI["text type"] == x][y].std()
        for x in sorted(dfAPI["text type"].unique())
    ]
    # dfSTATSttypes[y + " skew"] = [
    #     dfAPI.loc[dfAPI["text type"] == x][y].skew()
    #     for x in sorted(dfAPI["text type"].unique())
    # ]
    # dfSTATSttypes[y + " kurt"] = [
    #     dfAPI.loc[dfAPI["text type"] == x][y].kurt()
    #     for x in sorted(dfAPI["text type"].unique())
    # ]

#### SAVE FILES
dfAPI.to_csv("freqs_data.csv", index=False)
dfSTATSrels.to_csv("freqs_stats_rels.csv", index=False)
dfSTATSttypes.to_csv("freqs_stats_ttypes.csv", index=False)

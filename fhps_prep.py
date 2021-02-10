import pandas as pd
import numpy as np
import glob
import re

#### MAKE DATAFRAME
filesAPI = glob.glob("data/fhps/" + "*.npy")

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

        # add ref
        ref = int(re.findall(r"\d+", file)[0])
        temp["ref#"] = ref
        # get s.ids
        temp["s.id"] = re.findall(r"s#\d+",str(temp["Word"]))
        # get relevant columns to graph
        temp = temp.filter(["s.id", "frq", "fpm", "ref#"], axis=1)
        # append to dfAPI
        dfAPI = dfAPI.append(temp, sort=False)
    except:
        print("*** problem with " + file + " ***")

# presort by ref#
dfAPI = dfAPI.sort_values(by=["ref#"])

#### SAVE FILES
dfAPI.to_csv("fhps_data.csv", index=False)
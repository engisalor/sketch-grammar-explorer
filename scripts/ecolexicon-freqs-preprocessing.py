# get grammar
with open("grammar.txt") as f:
    lines = [line.rstrip() for line in f]
lines = lines[lines.index("### Pilar's relations start here") :]

# get indexes of CQL rules
cqllines = [i for i, x in enumerate(lines) if "[" in x]

# make dict of relations & CQL expressions
dt = {}
for i in range(0, len(cqllines)):
    rslice = reversed(lines[: cqllines[i]])
    relation = next((x for x in rslice if "#" in x), ["NA"])
    dt[cqllines[i]] = [relation, lines[cqllines[i]]]

# modify CQL rules
for x in dt:
    # change default attribute syntax ("N.*" to [tag="N.*"])
    dt[x][1] = re.sub('(?<!=)("[\|\.\*A-Z]+")', "[tag=\g<0>]", dt[x][1])
    # limit to within sentence
    dt[x][1] = dt[x][1] + " within <s/>"

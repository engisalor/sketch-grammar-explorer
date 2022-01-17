import re
import pathlib

import sge


def convert_grammar(input, dest):
    """
    Converts a sketch grammar into a list of SGE-formatted queries.

    Currently designed for the EcoLexicon Semantic Sketch Grammar - requires modification for other inputs.

    Assumes the following:

    - CQL rules are identified by the presence of at least one left bracket: e.g., "[lemma="ocean"]"
    - input is structured as in below:

    # <initial comments if any>

    *STRUCTLIMIT s
    *DEFAULTATTR tag

    *DUAL
    <valid word sketch relation type>

    # <rule label>

    <CQL rule>

    <... more relation types, labels and rules>
    """

    # Get grammar
    file = pathlib.Path(input)
    with open(file) as f:
        lines = [line.rstrip() for line in f]

    # Reformat grammar
    grammar = {}
    grammar["type"] = "freqs"

    rules = [
        i
        for i, line in enumerate(lines)
        if "[" in line and line[0] not in ["=", "#", "*"]
    ]

    for i in range(0, len(rules)):
        sliced = reversed(lines[: rules[i]])
        relation = next(
            (relation for relation in sliced if relation.startswith("#")), ["NA"]
        )
        type = [m.group() for l in sliced for m in [re.match("=.*", l)] if m][0]
        subs = [("=", ""), ('"%w"', ""), (".../ ", " / "), ("...", "")]
        for item in subs:
            type = type.replace(item[0], item[1]).strip()
            relation = relation.strip()
        grammar[str(i)] = {
            "type": type,
            "relation": relation,
            "call": {"q": lines[rules[i]]},
        }

    # Edit CQL rules
    for k, v in grammar.items():
        if k != "type":
            # Limit to within sentence
            v["call"]["q"] = "".join([v["call"]["q"], " within <s/>"])
            # Set the default attribute
            v["call"]["q"] = "".join(["atag,", v["call"]["q"]])

    # Complete first call parameters (modify for other grammars)
    call0 = {
        "q": grammar["0"]["call"]["q"],
        "corpname": "preloaded/ecolexicon_en",
        "freq_sort": "freq",
        "fcrit": ["doc.domains 0", "doc.genre 0", "doc.editor 0", "doc.user 0"],
    }

    grammar["0"]["call"] = call0

    sge.Parse(grammar, dest=dest)

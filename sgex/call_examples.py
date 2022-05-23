call_examples = {
    "collx": {
        "type": "collx",
        "meta": {"category1": "tag1"},
        "call": {
            "corpname": "preloaded/ecolexicon_en",
            "format": "json",
            "q": ['alemma_lc,"climate" within <doc (user="Expert") />'],
            "default_attr": "lemma_lc",
            "cmaxitems": 1000,
            "collpage": 1,
            "cattr": "lemma_lc",
            "cfromw": -3,
            "ctow": 3,
            "cbgrfns": ["d"],
            "cminfreq": 5,
            "cminbgr": 3,
            "csortfn": "d",
            "l": "climate",
        },
    },
    "freqs": {
        "type": "freqs",
        "meta": {"category1": "tag1"},
        "call": {
            "q": ['alemma,"rock"'],
            "corpname": "preloaded/ecolexicon_en",
            "freq_sort": "freq",
            "fcrit": ["doc.domains 0", "doc.genre 0", "doc.editor 0"],
        },
    },
    "view": {
        "type": "view",
        "meta": {"category1": "tag1"},
        "call": {
            "q": ['alemma,"ice"'],
            "corpname": "preloaded/ecolexicon_en",
            "viewmode": "sen",
            "pagesize": 20,
            "fromp": 1,
            "refs": "doc,s",
        },
    },
    "wsketch": {
        "type": "wsketch",
        "meta": {"category1": "tag1"},
        "call": {
            "lemma": "climate change",
            "lpos": "-n",
            "corpname": "preloaded/ecolexicon_en",
        },
    },
    "wordlist": {
        "type": "wordlist",
        "call": {
            "corpname": "preloaded/ecolexicon_en",
            "wltype": "simple",
            "wlattr": "lemma",
        },
    },
}

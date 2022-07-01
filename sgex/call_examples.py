call_examples = {
    "collx": {
        "type": "collx",
        "meta": ["a", "list", "of", "tags"],
        "call": {
            "corpname": "preloaded/ecolexicon_en",
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
    "freqs-rock": {
        "type": "freqs",
        "meta": {"text types": ["domain", "genre", "editor"]},
        "call": {
            "q": ['alemma,"rock"'],
            "corpname": "preloaded/ecolexicon_en",
            "freq_sort": "freq",
            "fcrit": ["doc.domains 0", "doc.genre 0", "doc.editor 0"],
        },
    },
    "freqs-stone": {
        "keep": "concsize",
        "meta": {"a tag": "that is added to previous ones"},
        "call": {
            "q": ['alemma,"stone"'],
        },
    },
    "freqml-whole_KWIC": {
        "type": "freqml",
        "call": {
            "q": [
                "atag, \"VVN\" \"N.*\""
            ],
            "corpname": "preloaded/ecolexicon_en",
            "fmaxitems": 50,
            "freq_sort": "freq",
            "flimit": 0,
            "ml1ctx": "0~0>0",
            "ml1attr": "word"
        }
    },
    "freqml-numbered-collocation": {
        "call": {
            "q": [
                "atag, 2:\"N.*\" 1:[word=\"improved\"] "
            ],
            "ml1ctx": "0>2"
        }
    },
    "view": {
        "type": "view",
        "call": {
            "q": ['alemma,"ice"'],
            "corpname": "preloaded/ecolexicon_en",
            "viewmode": "sen",
            "pagesize": 20,
            "fromp": 1,
            "refs": "doc,s",
            "asyn": 1,
        },
    },
    "wsketch": {
        "type": "wsketch",
        "meta": "a string for metadata",
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

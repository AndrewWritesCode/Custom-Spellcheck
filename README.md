# Custom-Spellcheck
Takes a list of words specified by user and spellchecks input text to that dictionary.

The current scorer is CPU-only and dependency-free. Each word is represented as a
sparse character n-gram vector, candidates are compared with cosine similarity,
and close matches are ranked with an edit-distance tie breaker.

Flow Chart of Valid Word Initialization & Word Selection
```mermaid
graph TD;
    A[valid word added]-->B[wordScore calculated];
    C[charScores used to determine character weights and dimensionality]-->B[wordScore calculated];
    B[wordScore calculated]-->D[wordScore and data associated with word stored in Valid Dictionary hash map];
    D[wordScore and data associated with word stored in Valid Dictionary hash map]-->E[WordBook];
    D-->A
    E[WordBook initialized]-->F[user input read];
    F[user input read]-->G[input wordScore calculated];
    G[input wordScore calculated]-->H[input wordScore compared to wordScores in Valid Dictionary];
    H[input wordScore compared to wordScores in Valid Dictionary]-->J[Valid Dictionary entry with closest wordScore match returned];
    J[Valid Dictionary entry with closest wordScore match returned]-->F[user input read];
```



<h3>Example (color_example.py):</h3>

```
import json

import custom_spellcheck as sc

with open('colors.json', encoding="utf-8") as json_file:
    colors = json.load(json_file)

color_book = sc.WordBook()
color_book.add_dictionary_to_WordBook(colors)

rgb = color_book.spellcheck_word("ponk")

print(rgb[0])

print(rgb[1])

print(color_book.spellcheck_word("ponk")[1]["RGB"])
```

<h3>Unchecked Input</h3>
INPUT (without Custom Spellcheck): `rgb = color_book["ponk"]["RGB"]`

OUTPUT: `Key Error`

<h3>Spellchecked Input</h3>
INPUT (with Custom Spellcheck): `rgb = color_book.spellcheck_word("ponk")[1]["RGB"]`

OUTPUT: `rgb = color_book["pink"]["RGB"]`

Note: `color_book.spellcheck_word("ponk")[1]` gets the information of the word (RGB in this case),
`color_book.spellcheck_word("ponk")[0]` is the word

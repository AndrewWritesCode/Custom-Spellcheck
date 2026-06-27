from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from math import sqrt


alph = 'abcdefghijklmnopqrstuvwxyz '
alph_numeric = 'abcdefghijklmnopqrstuvwxyz 0123456789'
comprehensive = 'abcdefghijklmnopqrstuvwxyz 0123456789!@#$%^&*()_-+={}[]|\\;:\'\",<.>/?'

_DEFAULT_NGRAM_WEIGHTS = {
    1: 0.2,
    2: 0.8,
    3: 1.0,
}


class WordScore(dict):
    """Sparse, normalized character n-gram vector used for word matching."""

    def dot(self, other):
        if len(self) > len(other) and hasattr(other, 'dot'):
            return other.dot(self)
        if len(self) > len(other):
            return sum(value * self.get(feature, 0.0) for feature, value in other.items())
        return sum(value * other.get(feature, 0.0) for feature, value in self.items())


# Generates a dictionary to store character scores based on input character.
# Kept for compatibility with the original public helper.
def charScores_generator(valid_chars=alph):
    char_index = {c: i for i, c in enumerate(valid_chars)}
    char_scores = [
        [1.0 if row == col else 0.0 for col in range(len(valid_chars))]
        for row in range(len(valid_chars))
    ]
    return char_scores, char_index


def _clean_text(input_text, valid_characters):
    valid = set(valid_characters)
    return ''.join(char for char in str(input_text).lower() if char in valid)


def _ngram_features(cleaned_text):
    if not cleaned_text:
        return ()

    padded = f'^{cleaned_text}$'
    features = []
    for ngram_size, weight in _DEFAULT_NGRAM_WEIGHTS.items():
        if len(padded) < ngram_size:
            continue
        for index in range(len(padded) - ngram_size + 1):
            features.append((f'{ngram_size}:{padded[index:index + ngram_size]}', weight))
    return features


def _sparse_word_score(input_text, valid_characters=alph, word_length_bias=1.0):
    cleaned_text = _clean_text(input_text, valid_characters)
    weights = defaultdict(float)

    for feature, weight in _ngram_features(cleaned_text):
        weights[feature] += weight

    if word_length_bias and cleaned_text:
        length_bucket = min(len(cleaned_text), 32)
        weights[f'len:{length_bucket}'] += 0.35 * word_length_bias

    norm = sqrt(sum(value * value for value in weights.values()))
    if not norm:
        return WordScore()

    return WordScore({feature: value / norm for feature, value in weights.items()})


# Defines a score for a word.
# The original implementation returned a NumPy vector. The rewritten scorer is
# stdlib-only and returns a sparse normalized vector with the same conceptual role.
def string_to_wordScore(input_text, char_matrix=None, char_index=None, word_length_bias=1.0):
    valid_characters = ''.join(char_index) if char_index else alph
    return _sparse_word_score(input_text, valid_characters, word_length_bias)


def _damerau_levenshtein_distance(left, right):
    left_len = len(left)
    right_len = len(right)

    if left == right:
        return 0
    if left_len == 0:
        return right_len
    if right_len == 0:
        return left_len

    previous_previous = None
    previous = list(range(right_len + 1))

    for left_index, left_char in enumerate(left, start=1):
        current = [left_index] + [0] * right_len
        for right_index, right_char in enumerate(right, start=1):
            insertion = current[right_index - 1] + 1
            deletion = previous[right_index] + 1
            substitution = previous[right_index - 1] + (left_char != right_char)
            current[right_index] = min(insertion, deletion, substitution)

            if (
                previous_previous is not None
                and left_index > 1
                and right_index > 1
                and left_char == right[right_index - 2]
                and left[left_index - 2] == right_char
            ):
                current[right_index] = min(
                    current[right_index],
                    previous_previous[right_index - 2] + 1,
                )

        previous_previous, previous = previous, current

    return previous[right_len]


def _edit_similarity(left, right):
    max_len = max(len(left), len(right), 1)
    return 1.0 - (_damerau_levenshtein_distance(left, right) / max_len)


def _length_similarity(left, right):
    max_len = max(len(left), len(right), 1)
    return 1.0 - (abs(len(left) - len(right)) / max_len)


class WordBook:
    def __init__(self, valid_characters=alph):
        self.wordBook = {}
        self.valid_characters = valid_characters
        self.charScoreMatrix, self.charIndex = charScores_generator(valid_characters)
        self.max_str_len = len(valid_characters)
        self._feature_index = defaultdict(set)
        self._clean_words = {}

    def _score_word(self, input_string):
        return string_to_wordScore(
            input_string,
            self.charScoreMatrix,
            self.charIndex,
        )

    def _remove_from_index(self, word):
        entry = self.wordBook.get(word)
        if not entry:
            return

        for feature in entry.get('wordScore', {}):
            indexed_words = self._feature_index.get(feature)
            if indexed_words is None:
                continue
            indexed_words.discard(word)
            if not indexed_words:
                del self._feature_index[feature]
        self._clean_words.pop(word, None)

    def _index_word(self, word):
        entry = self.wordBook[word]
        for feature in entry.get('wordScore', {}):
            self._feature_index[feature].add(word)
        self._clean_words[word] = _clean_text(word, self.valid_characters)

    def add_string_to_WordBook(self, input_string, force_lower=False):
        if force_lower:
            input_string = str(input_string).lower()

        self._remove_from_index(input_string)
        input_string_score = self._score_word(input_string)
        if input_string not in self.wordBook:
            self.wordBook[input_string] = {
                'word': input_string,
                'wordScore': input_string_score,
            }
        else:
            self.wordBook[input_string]['word'] = input_string
            self.wordBook[input_string]['wordScore'] = input_string_score
        self._index_word(input_string)

    def add_list_to_WordBook(self, input_list):
        for inputString in input_list:
            self.add_string_to_WordBook(inputString)

    def add_dictionary_to_WordBook(self, input_dictionary):
        for key, value in input_dictionary.items():
            if key in self.wordBook:
                self._remove_from_index(key)
                entry = self.wordBook[key]
            else:
                entry = {'word': str(key)}
                self.wordBook[key] = entry

            if isinstance(value, Mapping):
                entry.update(value)
            else:
                entry['value'] = value

            entry.setdefault('word', str(key))
            entry['wordScore'] = self._score_word(str(key))
            self._index_word(key)

    # TODO: deprecate this
    def recalculate_charScores(self):
        pass

    # TODO: deprecate this
    def export_charScores_to_json(self, path):
        pass

    # TODO: deprecate this
    def load_charScores_from_json(self, path):
        pass

    def recalculate_wordScores(self):
        self._feature_index.clear()
        self._clean_words.clear()
        for key in self.wordBook:
            self.wordBook[key]['wordScore'] = self._score_word(str(key))
            self._index_word(key)

    def add_info_to_WordBook_entry(self, word, info_key, info, overwrite=False):
        if info_key not in self.wordBook[word]:
            self.wordBook[word][info_key] = info
        elif overwrite:
            self.wordBook[word][info_key] = info

    def _candidate_words(self, score):
        candidates = set()
        for feature in score:
            candidates.update(self._feature_index.get(feature, ()))
        return candidates or set(self.wordBook)

    def _rank_candidate(self, input_text, cleaned_input, input_score, candidate):
        entry = self.wordBook[candidate]
        candidate_score = entry.get('wordScore')
        if candidate_score is None:
            candidate_score = self._score_word(str(candidate))
            entry['wordScore'] = candidate_score
            self._index_word(candidate)

        cosine_similarity = input_score.dot(candidate_score) if input_score else 0.0
        cleaned_candidate = self._clean_words.get(candidate)
        if cleaned_candidate is None:
            cleaned_candidate = _clean_text(candidate, self.valid_characters)
            self._clean_words[candidate] = cleaned_candidate

        edit_similarity = _edit_similarity(cleaned_input, cleaned_candidate)
        length_similarity = _length_similarity(cleaned_input, cleaned_candidate)
        combined_score = (
            0.70 * cosine_similarity
            + 0.25 * edit_similarity
            + 0.05 * length_similarity
        )

        exact_case_match = str(input_text) == str(candidate)
        exact_clean_match = cleaned_input == cleaned_candidate
        return (
            combined_score,
            cosine_similarity,
            edit_similarity,
            length_similarity,
            exact_case_match,
            exact_clean_match,
            -len(str(candidate)),
        )

    def spellcheck_word(self, input_text):
        input_text = str(input_text)
        if input_text in self.wordBook:
            return input_text, self.wordBook[input_text]
        if not self.wordBook:
            return '', {}

        input_score = self._score_word(input_text)
        cleaned_input = _clean_text(input_text, self.valid_characters)

        candidates = self._candidate_words(input_score)
        closest_match = max(
            candidates,
            key=lambda candidate: self._rank_candidate(
                input_text,
                cleaned_input,
                input_score,
                candidate,
            ),
        )
        return str(closest_match), self.wordBook[closest_match]

    def __iter__(self):
        return iter(self.wordBook)

    def __add__(self, other):
        if not isinstance(other, WordBook):
            raise ValueError('Only WordBooks can be added to other WordBooks!')
        for word, entry in other.wordBook.items():
            self._remove_from_index(word)
            self.wordBook[word] = entry.copy()
            self._index_word(word)
        return self

    def __str__(self):
        return str(self.wordBook)

    def __getitem__(self, item):
        return self.wordBook[item]

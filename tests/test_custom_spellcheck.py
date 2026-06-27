import unittest

import custom_spellcheck as sc


class WordBookTests(unittest.TestCase):
    def test_spellcheck_returns_closest_word_and_entry_tuple(self):
        word_book = sc.WordBook()
        word_book.add_list_to_WordBook(['pink', 'purple', 'blue'])

        word, entry = word_book.spellcheck_word('ponk')

        self.assertEqual(word, 'pink')
        self.assertEqual(entry['word'], 'pink')
        self.assertIn('wordScore', entry)

    def test_dictionary_entries_keep_metadata(self):
        word_book = sc.WordBook()
        word_book.add_dictionary_to_WordBook({
            'pink': {'RGB': [255, 192, 203]},
            'blue': {'RGB': [0, 0, 255]},
        })

        word, entry = word_book.spellcheck_word('ponk')

        self.assertEqual(word, 'pink')
        self.assertEqual(entry['RGB'], [255, 192, 203])

    def test_existing_dictionary_entry_metadata_is_preserved(self):
        word_book = sc.WordBook()
        word_book.add_string_to_WordBook('helium')
        word_book.add_info_to_WordBook_entry('helium', 'AtomicNumber', 2)
        word_book.add_dictionary_to_WordBook({'helium': {'Symbol': 'He'}})

        self.assertEqual(word_book['helium']['AtomicNumber'], 2)
        self.assertEqual(word_book['helium']['Symbol'], 'He')

    def test_force_lower_preserves_legacy_behavior(self):
        word_book = sc.WordBook()
        word_book.add_string_to_WordBook('Pink', force_lower=True)

        self.assertIn('pink', word_book.wordBook)
        self.assertEqual(word_book.spellcheck_word('PINK')[0], 'pink')

    def test_empty_wordbook_returns_empty_tuple_shape(self):
        word_book = sc.WordBook()

        self.assertEqual(word_book.spellcheck_word('anything'), ('', {}))


if __name__ == '__main__':
    unittest.main()

from django.test import TestCase

from App.controllers import TextCleaner, CosineSimilarityCalculator, ClusterMaker


class TextCleanerTestCase(TestCase):
    def setUp(self) -> None:
        ...

    def test_html_entities_method(self):
        text = 'this is &copy; 2022'
        expected = 'this is  2022'

        c = TextCleaner(text)
        c.html_entities()

        self.assertEqual(c.text, expected)

    def test_html_tags_method(self):
        text = '<a href="https://google.com">This is link</a>'
        expected = 'This is link'

        c = TextCleaner(text)
        c.html_tags()

        self.assertEqual(c.text, expected)

    def test_emails_method(self):
        text = 'mohamed email is xxx_dd33@gmail.com'
        expected = 'mohamed email is'

        c = TextCleaner(text)
        c.emails()

        self.assertEqual(c.text, expected)

    def test_usernames_method(self):
        text = 'my username @d3v.mhmd'
        expected = 'my username'

        c = TextCleaner(text)
        c.usernames()

        self.assertEqual(c.text, expected)

    def test_links_method(self):
        text = 'youtube link https://www.youtube.com/watch?v=JyKPUtV1bN4&ab_channel=AlJazeeraMubasher%D9%82%D9%86%D8%A7%D8%A9%D8%A7%D9%84%D8%AC%D8%B2%D9%8A%D8%B1%D8%A9%D9%85%D8%A8%D8%A7%D8%B4%D8%B1'
        expected = 'youtube link'

        c = TextCleaner(text)
        c.links()

        self.assertEqual(c.text, expected)

    def test_lowercase_method(self):
        text = 'THIS IS MHMD'
        expected = 'this is mhmd'

        c = TextCleaner(text)
        c.lowercase()

        self.assertEqual(c.text, expected)

    def test_hashtags_method(self):
        text = 'i like #pizza'
        expected = 'i like'

        c = TextCleaner(text)
        c.hashtags()

        self.assertEqual(c.text, expected)

    def test_repeating_chars_method(self):
        text = 'this is xxxx.cmcm. play'
        expected = 'this is .cmcm. play'

        c = TextCleaner(text)
        c.repeating_chars()

        self.assertEqual(c.text, expected)

    def test_not_letters_method(self):
        text = '\t\t\nThis-\t\t-*-*/-*/*-/-* Mhmd'
        expected = 'This \t\t              Mhmd'

        c = TextCleaner(text)
        c.not_letters()

        self.assertEqual(c.text, expected)

    def test_underscore_method(self):
        text = 'mhdm_____ali__lsk lks'
        expected = 'mhdm     ali  lsk lks'

        c = TextCleaner(text)
        c.underscore()

        self.assertEqual(c.text, expected)

    def test_numbers_method(self):
        text = 'this is 984532121 askjl 456 321sdlk 132'
        expected = 'this is           askjl        sdlk'

        c = TextCleaner(text)
        c.numbers()

        self.assertEqual(c.text, expected)

    def test_lines_method(self):
        text = 'mhmd\n\nali\n\nmhmd'
        expected = 'mhmd  ali  mhmd'

        c = TextCleaner(text)
        c.lines()

        self.assertEqual(c.text, expected)

    def test_shorter_than_method(self):
        text = 'bla l l l l bla bla bb sss'
        expected = 'bla     bla bla bb sss'

        c = TextCleaner(text)
        c.shorter_than()

        self.assertEqual(c.text, expected)

    def test_stop_words_method(self):
        text = 'mohamed and ali are amazing for the team'
        expected = 'mohamed  ali  amazing   team'

        c = TextCleaner(text)
        c.stop_words()

        self.assertEqual(c.text, expected)

    def test_double_spaces_method(self):
        text = 'this is           askjl        sdlk'
        expected = 'this is askjl sdlk'

        c = TextCleaner(text)
        c.double_spaces()

        self.assertEqual(c.text, expected)

    # def test_stemming_method(self):
    #     text = ''
    #     expected = ''
    #     c = TextCleaner(text)
    #     c.stemming()
    #     self.assertEqual(c.text, expected)

    def test_uncamelcase_method(self):
        text = 'Name varOneTwo and varTwo TowThree, This is insane'
        expected = 'Name var One Two and var Two Tow Three, This is insane'

        c = TextCleaner(text)
        c.uncamelcase()

        self.assertEqual(c.text, expected)

    def test__get_language_method(self):
        text = 'This is english'
        expected = 'english'

        c = TextCleaner(text)
        self.assertEqual(c._get_language(), expected)

        text = 'هذا النص عربي'
        expected = 'arabic'

        c = TextCleaner(text)
        self.assertEqual(c._get_language(), expected)

    def test_full_clean_method(self):
        text = 'Just make sure no issues showed'
        # expected = ''
        c = TextCleaner(text)
        c.full_clean()
        # self.assertEqual(c.text, expected)


class CosineSimilarityCalculatorTestCase(TestCase):
    def setUp(self) -> None:
        documents = [
            {'red': 5, 'blue': 4},
            {'doctor': 2, 'blood': 11, 'red': 50},
        ]
        self.obj = CosineSimilarityCalculator(documents)

    def test__unique_words_property(self):
        keys = ['red', 'blue', 'doctor', 'blood']
        self.assertEqual(len(self.obj._unique_words), 4)
        self.assertTrue(
            all([
                item in self.obj._unique_words
                for item in keys
            ])
        )

    def test__doc_to_word_weight_matrix_property(self):
        self.assertEqual(
            self.obj._doc_to_word_weight_matrix.shape, (2, 4)
        )

    def test_similarity_method(self):
        # make sure it just work
        self.obj.similarity()


class ClusterMakerTestCase(TestCase):
    def setUp(self) -> None:
        documents = ['doc1', 'doc2']
        similarity = [
            [1, 0.76204993],
            [0.76204993, 1]
        ]
        self.obj = ClusterMaker(documents, similarity, 0.4)

    def test_clusters_method(self):
        self.obj.clusters()

    def test_clusters_flat_method(self):
        self.obj.clusters_flat()

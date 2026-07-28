import re


class VocabCEFRClassifier:
    def predict_cefr(self, word: str) -> str:
        word = word.lower().strip()
        length = len(word)
        syllables = len(re.findall(r'[aeiouy]+', word))

        if length <= 4 and syllables <= 1:
            return "A1"
        elif length <= 6 and syllables <= 2:
            return "A2"
        elif length <= 8 and syllables <= 3:
            return "B1"
        elif length <= 10 and syllables <= 4:
            return "B2"
        elif length <= 12:
            return "C1"
        else:
            return "C2"
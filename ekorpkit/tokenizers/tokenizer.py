import logging
from abc import ABCMeta, abstractmethod
from ..preprocessors.normalizer import strict_normalize, only_text

logger = logging.getLogger(__name__)


class Tokenizer:
    __metaclass__ = ABCMeta

    def __init__(
        self,
        **kwargs,
    ):
        self.only_text = kwargs.get("only_text", True)
        self.tokenize_each_word = kwargs.get("tokenize_each_word", False)
        self.wordpieces_prefix = kwargs.get("wordpieces_prefix", "##")
        self.noun_pos = kwargs.get("noun_pos", None)
        if self.noun_pos is None:
            self.noun_pos = ["NNG", "NNP", "XSN", "SL", "XR", "NNB", "NR"]
        self.token_xpos_filter = kwargs.get("token_xpos_filter", None)
        if self.token_xpos_filter is None:
            self.token_xpos_filter = ["SP"]
        self.no_space_for_non_nouns = kwargs.get("no_space_for_non_nouns", False)

    @abstractmethod
    def parse(self, text):
        raise NotImplementedError("Must override pos")

    def tokenize(self, text):
        if self.only_text:
            text = only_text(strict_normalize(text))
        if self.tokenize_each_word:
            term_pos = []
            for word in text.split():
                term_pos += self._tokenize_word(word)
            return term_pos
        else:
            text = " ".join(text.split())
            return self.parse(text)

    def _tokenize_word(self, word):
        tokens = self.parse(word)
        term_pos = []
        for i, (term, pos) in enumerate(tokens):
            if i == 0:
                term_pos.append(f"{term}/{pos}")
            else:
                term_pos.append(f"{self.wordpieces_prefix}{term}/{pos}")
        return term_pos

    def nouns(self, text):
        tokenized_text = self.tokenize(text)
        return extract_tokens(
            tokenized_text, nouns_only=True, noun_pos_filter=self.noun_pos
        )

    def tokens(self, text):
        tokenized_text = self.tokenize(text)
        return extract_tokens(
            tokenized_text,
            nouns_only=False,
            token_xpos_filter=self.token_xpos_filter,
            no_space_for_non_nouns=self.no_space_for_non_nouns,
        )


class PynoriTokenizer(Tokenizer):
    def __init__(
        self,
        args=None,
        **kwargs,
    ):
        logging.warning("Initializing Pynori...")
        try:
            from pynori.korean_analyzer import KoreanAnalyzer

            self._tokenizer = KoreanAnalyzer(**args)
        except ImportError:
            raise ImportError(
                "\n"
                "You must install `pynori` if you want to use `pynori` backend.\n"
                "Please install using `pip install pynori`.\n"
            )
        super().__init__(**kwargs)

    def parse(self, text):

        tokens = self._tokenizer.do_analysis(text)
        term_pos = [
            f"{term}/{pos}" for term, pos in zip(tokens["termAtt"], tokens["posTagAtt"])
        ]
        return term_pos


class MecabTokenizer(Tokenizer):
    def __init__(
        self,
        args=None,
        **kwargs,
    ):

        logging.warning("Initializing mecab...)")
        try:
            from .mecab import MeCab

            self._tokenizer = MeCab(**args)
        except ImportError:
            raise ImportError(
                "\n"
                "You must install `fugashi` and `mecab_ko_dic` if you want to use `mecab` backend.\n"
                "Please install using `pip install python-mecab-ko`.\n"
            )
        super().__init__(**kwargs)

    def parse(self, text):
        return self._tokenizer.pos(text)


class BWPTokenizer(Tokenizer):
    def __init__(
        self,
        args=None,
        **kwargs,
    ):
        logging.warning("Initializing BertWordPieceTokenizer...")
        try:
            from transformers import BertTokenizerFast

            self._tokenizer = BertTokenizerFast.from_pretrained(**args)

        except ImportError:
            raise ImportError(
                "\n"
                "You must install `BertWordPieceTokenizer` if you want to use `bwp` backend.\n"
                "Please install using `pip install transformers`.\n"
            )
        super().__init__(**kwargs)

    def parse(self, text):
        return self._tokenizer.tokenize(text)


def extract_tokens(
    tokenized_text,
    nouns_only=False,
    noun_pos_filter=["NNG", "NNP", "XSN", "SL", "XR", "NNB", "NR"],
    token_xpos_filter=["SP"],
    no_space_for_non_nouns=False,
    **kwargs,
):

    _tokens_pos = [
        token.split("/")
        for token in tokenized_text.split()
        if len(token.split("/")) == 2
    ]

    if nouns_only:
        _tokens = [
            token[0].strip() for token in _tokens_pos if token[1] in noun_pos_filter
        ]
    else:
        exist_sp_tag = False
        for i, token in enumerate(_tokens_pos):
            if token[1] == "SP":
                exist_sp_tag = True
                break

        _tokens = []
        if exist_sp_tag and no_space_for_non_nouns:
            prev_nonnoun_check = False
            cont_morphs = []
            i = 0
            while i < len(_tokens_pos):
                token = _tokens_pos[i]
                if not prev_nonnoun_check and token[1] in noun_pos_filter:
                    _tokens.append(token[0])
                elif (
                    not prev_nonnoun_check
                    and token[1] not in noun_pos_filter
                    and token[1][0] != "S"
                ):
                    prev_nonnoun_check = True
                    cont_morphs.append(token[0])
                elif (
                    prev_nonnoun_check
                    and token[1] not in noun_pos_filter
                    and token[1][0] != "S"
                ):
                    cont_morphs.append(token[0])
                else:
                    if len(cont_morphs) > 0:
                        _tokens.append("".join(cont_morphs))
                        cont_morphs = []
                        prev_nonnoun_check = False
                    if token[1] != "SP":
                        _tokens.append(token[0])
                i += 1
            if len(cont_morphs) > 0:
                _tokens.append("".join(cont_morphs))
        else:
            _tokens = [
                token[0].strip()
                for token in _tokens_pos
                if token[1] not in token_xpos_filter
            ]
    return _tokens


# def extract_tokens_dataframe(df, **args):
#     x_args = args["extract_func"]
#     text_key = x_args["text_key"]
#     num_workers = args["num_workers"]

#     def extact_tokens_row(row):
#         text = row[text_key]
#         if not isinstance(text, str):
#             return None

#         sents = []
#         for sent in text.split("\n"):
#             if len(sent) > 0:
#                 tokens = extract_tokens(sent, **x_args)
#                 token_sent = " ".join(tokens)
#                 sents.append(token_sent)
#             else:
#                 sents.append("")
#         return "\n".join(sents)

#     df[text_key] = df.apply(extact_tokens_row, axis=1)

#     df = df.dropna(subset=[text_key])
#     return df

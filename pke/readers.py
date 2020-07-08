#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Readers for the pke module."""

import xml.etree.ElementTree as etree
import spacy

from pke.data_structures import Document
from nltk.tag import CRFTagger
from nltk.tokenize import sent_tokenize, word_tokenize, TweetTokenizer
from nltk.corpus import stopwords
import string
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
ct = CRFTagger()
ct.set_model_file('./all_indo_man_tag_corpus_model.crf copy.tagger')
factory = StemmerFactory()
stemmer = factory.create_stemmer()
tokenizer_words = TweetTokenizer()


class Reader(object):
    def read(self, path):
        raise NotImplementedError


class MinimalCoreNLPReader(Reader):
    """Minimal CoreNLP XML Parser."""

    def __init__(self):
        self.parser = etree.XMLParser()

    def read(self, path, **kwargs):
        sentences = []
        tree = etree.parse(path, self.parser)
        for sentence in tree.iterfind('./document/sentences/sentence'):
            # get the character offsets
            starts = [int(u.text) for u in
                      sentence.iterfind("tokens/token/CharacterOffsetBegin")]
            ends = [int(u.text) for u in
                    sentence.iterfind("tokens/token/CharacterOffsetEnd")]
            sentences.append({
                "words": [u.text for u in
                          sentence.iterfind("tokens/token/word")],
                "lemmas": [u.text for u in
                           sentence.iterfind("tokens/token/lemma")],
                "POS": [u.text for u in sentence.iterfind("tokens/token/POS")],
                "char_offsets": [(starts[k], ends[k]) for k in
                                 range(len(starts))]
            })
            sentences[-1].update(sentence.attrib)

        doc = Document.from_sentences(sentences, input_file=path, **kwargs)

        return doc


class RawTextReader(Reader):
    """Reader for raw text."""

    def __init__(self, language=None):
        """Constructor for RawTextReader.

        Args:
            language (str): language of text to process.
        """

        self.language = language

        if language is None:
            self.language = 'en'

    def read(self, text, **kwargs):
        """Read the input file and use spacy to pre-process.

        Args:
            text (str): raw text to pre-process.
            max_length (int): maximum number of characters in a single text for
                spacy, default to 1,000,000 characters (1mb).
        """
        if self.language != 'id':
            max_length = kwargs.get('max_length', 10**6)
            nlp = spacy.load(self.language,
                            max_length=max_length)
            spacy_doc = nlp(text)
            sentences = []
            for sentence_id, sentence in enumerate(spacy_doc.sents):
                sentences.append({
                    "words": [token.text for token in sentence],
                    "lemmas": [token.lemma_ for token in sentence],
                    "POS": [token.pos_ for token in sentence],
                    "char_offsets": [(token.idx, token.idx + len(token.text))
                                        for token in sentence]
                })
            
        else:
            text = text.lower()
            token_words = [tokenizer_words.tokenize(t) for t in sent_tokenize(text)]
            token_lemmas = []
            token_pos = ct.tag_sents(token_words)

            for token in token_words:
                temp = []
                for word in token:
                    temp.append(stemmer.stem(word))
                token_lemmas.append(temp)
            
            sentences = []
            for idx, _ in enumerate(token_words):
                sentences.append({
                            "words": token_words[idx],
                            "lemmas": token_lemmas[idx],
                            "POS": token_pos[idx],
                        })
        doc = Document.from_sentences(sentences,
                                        input_file=kwargs.get('input_file', None),
                                        **kwargs)

        return doc


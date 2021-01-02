"""
tool to analyze top words from stackoverflow data
"""

import argparse
import json
import logging
import re
from collections import defaultdict, namedtuple
from typing import Dict, List, Set
from xml.etree import ElementTree

DATE_TAG = "CreationDate"
POST_TYPE_TAG = "PostTypeId"
QUESTION_TYPE = 1
SCORE_TAG = "Score"
STACKOVERFLOW_ENCODING = "utf-8"
STOPWORDS_ENCODING = "koi8-r"
TITLE_TAG = "Title"
WORD_RE = re.compile(r"\w+")


PostData = namedtuple("PostData", ["year", "post_type", "score", "title"])
QueryData = namedtuple("QueryData", ["start", "end", "top"])
logger = logging.getLogger("stackoverflow_logger")


class WordScore:
    """
    Class for compare result
    """
    def __init__(self, word, score):
        """
        Class constructor
        :param word: word from title
        :param score: total score for word
        """
        self.word = word
        self.score = score

    def __lt__(self, other):

        if self.score < other.score:
            return True
        elif self.score == other.score:
            return self.word > other.word
        return False


def parse_xml(string: str) -> PostData:
    """
    Convert xml string to namedtuple
    :param string: xml string
    :return: namedtuple with start, end, rating and title
    """
    xml_tree = ElementTree.fromstring(string)
    result = PostData(
        year=int(xml_tree.attrib.get(DATE_TAG)[:4]),
        post_type=int(xml_tree.attrib.get(POST_TYPE_TAG)),
        score=int(xml_tree.attrib.get(SCORE_TAG)),
        title=xml_tree.attrib.get(TITLE_TAG, "")
    )
    return result


def get_words(string: str) -> List[str]:
    """
    Function to extract words from sentence
    :param string: sentence
    :return: list of words in lower register
    """
    return WORD_RE.findall(string.lower())


def load_data(filepath: str) -> Dict[int, Dict[str, int]]:
    """
    Function to load documents in xml_row format in convert it to dict with scores
    :param filepath: path to file with xml rows
    :return: list of parsed xml rows
    """
    result = defaultdict(dict)
    with open(filepath, "r", encoding=STACKOVERFLOW_ENCODING) as fio:
        for row in fio:
            xml_info = parse_xml(row.rstrip())
            if xml_info.post_type == QUESTION_TYPE:
                words = get_words(xml_info.title)
                for word in set(words):
                    if word in result[xml_info.year]:
                        result[xml_info.year][word] += xml_info.score
                    else:
                        result[xml_info.year][word] = xml_info.score
    logger.info("process XML dataset, ready to serve queries")
    return result


def load_stopwords(filepath: str) -> Set[str]:
    """
    Function for loading stopwords
    :param filepath: path to stopwords file
    :return: list of stopwords
    """
    result = set()
    with open(filepath, "r", encoding=STOPWORDS_ENCODING) as fio:
        for row in fio:
            result.add(row.rstrip().lower())
    return result


def load_query(filepath: str) -> List[QueryData]:
    """
    Function for loading queries
    :param filepath: filepath to queries
    :return:
    """
    result = []
    with open(filepath, "r", encoding=STOPWORDS_ENCODING) as fio:
        for row in fio:
            result.append(QueryData(*map(int, row.rstrip().split(","))))
    return result


def proceed_query(data: Dict[int, Dict[str, int]],
                  stopwords: Set[str],
                  query: QueryData) -> dict:
    """
    Function for proceed query in given data
    :param data: parsed xml data
    :param stopwords: set of stopwords
    :param query: query to proceed
    :return: answer dict
    """
    logger.debug(f'got query "{query.start},{query.end},{query.top}"')
    result = defaultdict(int)
    for year in range(query.start, query.end + 1):
        if year in data:
            for word, score in data[year].items():
                if word not in stopwords:
                    result[word] += score
    result = sorted([WordScore(k, v) for k, v in result.items()], reverse=True)
    if len(result) < query.top:
        message = f'not enough data to answer, found {len(result)} words out of {query.top} ' \
                  f'for period "{query.start},{query.end}"'
        logger.warning(message)
    result = {
        "start": query.start,
        "end": query.end,
        "top": [[var.word, var.score] for var in result[:query.top]]
    }
    return result


def setup_parser(parser: argparse.ArgumentParser) -> None:
    """
    Function for setup command line parser arguments
    :param parser: parser for arguments
    :return: Nothing
    """
    parser.add_argument("--questions", dest="data_path",
                        help="path to file with stackoverflow data")
    parser.add_argument("--stop-words", dest="stopwords_path",
                        help="path to file with words to exclude from analysis")
    parser.add_argument("--queries", dest="queries_path",
                        help="path to file with queries for analysis")


def setup_logging():
    logger.setLevel(logging.DEBUG)
    formater = logging.Formatter('%(levelname)s: %(message)s')
    main_handler = logging.FileHandler("stackoverflow_analytics.log")
    main_handler.setLevel(logging.DEBUG)
    main_handler.setFormatter(formater)
    warn_handler = logging.FileHandler("stackoverflow_analytics.warn")
    warn_handler.setLevel(logging.WARNING)
    warn_handler.setFormatter(formater)
    logger.addHandler(main_handler)
    logger.addHandler(warn_handler)


def main():
    """
    point of entry for module
    :return: Nothing
    """
    parser = argparse.ArgumentParser(
        prog="stackoverflow analytics",
        description="tool to analyze top words from stackoverflow data"
    )
    setup_parser(parser)
    setup_logging()
    arguments = parser.parse_args()
    parsed_data = load_data(arguments.data_path)
    stopwords = load_stopwords(arguments.stopwords_path)
    queries = load_query(arguments.queries_path)
    for query in queries:
        print(json.dumps(proceed_query(parsed_data, stopwords, query)))
    logger.info("finish processing queries")


if __name__ == "__main__":
    main()

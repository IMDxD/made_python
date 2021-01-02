import pytest
from textwrap import dedent

from task_Nesterenko_Anton_stackoverflow_analytics import get_words, load_data, load_query,\
    load_stopwords, parse_xml, proceed_query, PostData, QueryData

XML_STRING1 = '<row Id="206320" PostTypeId="1" AcceptedAnswerId="206399" ' \
              'CreationDate="2008-10-15T20:31:15.640" Score="13" ViewCount="16631" ' \
              'OwnerUserId="21539" ' \
              'OwnerDisplayName="zhinker" LastEditorUserId="63550" ' \
              'LastEditorDisplayName="brian d foy" LastEditDate="2013-09-04T07:27:07.790" ' \
              'LastActivityDate="2014-04-05T15:04:34.577" ' \
              'Title="How do I distinguish a file from a directory in Perl?" ' \
              'Tags="&lt;perl&gt;&lt;file&gt;&lt;directory&gt;" ' \
              'AnswerCount="6" CommentCount="0" FavoriteCount="4" />	'
XML_STRING2 = '<row Id="201905" PostTypeId="2" ParentId="201323" ' \
              'CreationDate="2008-10-14T16:35:44.180" Score="38" ' \
              'OwnerUserId="27886" OwnerDisplayName="adnam" ' \
              'LastActivityDate="2008-10-14T16:35:44.180" CommentCount="3" ' \
              'CommunityOwnedDate="2009-12-16T00:37:16.437" />'
PARSED_XML1 = PostData(2008, 1, 13, "How do I distinguish a file from a directory in Perl?")
PARSED_XML2 = PostData(2008, 2, 38, "")
TINY_DATASET_PATH = "dataset_tiny.xml"
TINY_DATASET_PARSED = {
    2008: {
        "how": 86,
        "do": 74,
        "i": 74,
        "write": 74,
        "a": 74,
        "short": 74,
        "literal": 74,
        "in": 86,
        "c": 74,
        "does": 12,
        "the": 12,
        "ls": 12,
        "command": 12,
        "work": 12,
        "linux": 12,
        "unix": 12
    },
    2009: {
        "setting": 5,
        "style": 5,
        "on": 5,
        "first": 5,
        "and": 5,
        "last": 5,
        "visible": 5,
        "tabitem": 5,
        "of": 5,
        "tabcontrol": 5
    }
}
STOPWORDS_DATA_STR = dedent("""\
    мои
    стоп
    слова
    my
    sTop
    wordS
""")
QUERIES_DATA_STR = dedent("""\
    2008,2009,10
    2018,2020,100
""")


@pytest.mark.parametrize(
    "string, result",
    [
        pytest.param(XML_STRING1, PARSED_XML1),
        pytest.param(XML_STRING2, PARSED_XML2),
    ]
)
def test_parse_xml(string, result):
    assert parse_xml(string) == result, "Wrong result of parsing"


@pytest.mark.parametrize(
    "string, result",
    [
        pytest.param("How do I distinguish a file from a directory in Perl?",
                     ["how", "do", "i", "distinguish", "a", "file", "from", "a", "directory", "in", "perl"]),
        pytest.param("", []),
    ]
)
def test_get_words(string, result):
    assert get_words(string) == result, "Wrong result of parsing"


def test_load_data():
    assert load_data(TINY_DATASET_PATH) == TINY_DATASET_PARSED


def test_load_stopwords(tmpdir):
    tmp_file = tmpdir.join('test.txt')
    with open(tmp_file, "w", encoding="koi8-r") as file:
        file.write(STOPWORDS_DATA_STR)
    etalon_stopwords = {"мои", "стоп", "слова", "my", "stop", "words"}
    assert load_stopwords(tmp_file) == etalon_stopwords


def test_load_queries(tmpdir):
    tmp_file = tmpdir.join('test.txt')
    with open(tmp_file, "w") as file:
        file.write(QUERIES_DATA_STR)
    etalon_queries = [
        QueryData(2008, 2009, 10),
        QueryData(2018, 2020, 100)
    ]
    assert load_query(tmp_file) == etalon_queries


@pytest.mark.parametrize(
    "query, answer",
    [
        pytest.param(QueryData(2008, 2009, 10), {
            "start": 2008,
            "end": 2009,
            "top": [
                ["how", 86],
                ["in", 86],
                ["c", 74],
                ["do", 74],
                ["i", 74],
                ["literal", 74],
                ["short", 74],
                ["write", 74],
                ["command", 12],
                ["does", 12]
            ]
        }),
        pytest.param(QueryData(2018, 2020, 100), {"start": 2018, "end": 2020, "top": []}),
    ]
)
def test_proceed_queries(query, answer):
    stopwords = {"мои", "стоп", "слова", "my", "stop", "words", "a"}
    result = proceed_query(TINY_DATASET_PARSED, stopwords, query)
    assert result == answer

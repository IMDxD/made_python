import os
from argparse import Namespace
from textwrap import dedent

import pytest

from inverted_index import InvertedIndex, load_documents, build_inverted_index

DATASET_TINY_PATH = '../resources/wikipedia_tiny'
DATASET_SMALL_PATH = '../resources/wikipedia_small'
DATASET_BIG_PATH = '../resources/wikipedia_sample'
DATASET_TINY_STR = dedent("""\
    123 Show must go on!
    321 Still loving you
    547 The Adventures of Rain Dance Maggie
    645 The House of Rising Son
    789 A A B
""")
ETALON_TINY_INDEX = {
    "Show": [123],
    "must": [123],
    "go": [123],
    "on!": [123],
    "Still": [321],
    "loving": [321],
    "you": [321],
    "The": [547, 645],
    "Adventures": [547],
    "of": [547, 645],
    "Rain": [547],
    "Dance": [547],
    "Maggie": [547],
    "House": [645],
    "Rising": [645],
    "Son": [645],
    "A": [789],
    "B": [789]
}


@pytest.fixture()
def tiny_dataset_fio(tmpdir):
    dataset_fio = tmpdir.join("dataset.txt")
    dataset_fio.write(DATASET_TINY_STR)
    return dataset_fio


@pytest.mark.parametrize(
    "datapath, length",
    [
        pytest.param(DATASET_TINY_PATH, 2),
        pytest.param(DATASET_SMALL_PATH, 4),
    ]
)
def test_can_run_load_documents(datapath,  length):
    docs = load_documents(datapath)
    assert length == len(docs), f"Wrong loaded length with file {datapath}, expected {length}, got {len(docs)}"


def test_error_load_documents_wrong_filepath():
    with pytest.raises(FileNotFoundError):
        load_documents("impresed")


def test_load_documents_do_correct(tiny_dataset_fio):
    documents = load_documents(tiny_dataset_fio)
    etalon_document = {
        123: "Show must go on!",
        321: "Still loving you",
        547: "The Adventures of Rain Dance Maggie",
        645: "The House of Rising Son",
        789: "A A B"
    }
    assert documents == etalon_document, "Dataset loaded incorrectly"


@pytest.mark.parametrize(
    "datapath",
    [
        DATASET_TINY_PATH,
        DATASET_SMALL_PATH
    ]
)
def test_can_run_build_index(datapath):
    documents = load_documents(datapath)
    build_inverted_index(documents)


def test_inverted_index_can_build():
    inverted_index = InvertedIndex(ETALON_TINY_INDEX)
    assert inverted_index._index == ETALON_TINY_INDEX, "Wrong class construction for inverted index"


def test_can_build_index_do_correct(tiny_dataset_fio):
    documents = load_documents(tiny_dataset_fio)
    inverted_index = build_inverted_index(documents)
    assert inverted_index._index == ETALON_TINY_INDEX, "Wrong build for inverted index"


@pytest.mark.parametrize(
    "query, answer",
    [
        pytest.param(["Show"], [123]),
        pytest.param(["The"], [547, 645]),
        pytest.param(["The", "Adventures"], [547]),
        pytest.param(["Unforgiven"], []),
    ]
)
def test_query_return_right_answer(tiny_dataset_fio, query, answer):
    documents = load_documents(tiny_dataset_fio)
    inverted_index = build_inverted_index(documents)
    assert sorted(answer) == sorted(inverted_index.query(query))


def test_inverted_index_can_dump_index(tiny_dataset_fio, tmpdir):
    documents = load_documents(tiny_dataset_fio)
    inverted_index = build_inverted_index(documents)
    tmp_fio = tmpdir.join('test.dump')
    inverted_index.dump(tmp_fio)
    assert os.path.isfile(tmp_fio), "File was not created"


def test_inverted_index_can_dump_load_index(tiny_dataset_fio, tmpdir):
    documents = load_documents(DATASET_BIG_PATH)
    inverted_index = build_inverted_index(documents)
    tmp_fio = tmpdir.join('test.dump')
    inverted_index.dump(tmp_fio)
    loaded_index = inverted_index.load(tmp_fio)
    assert inverted_index._index == loaded_index._index, "File was not created"


def test_inverted_index_load_wrong_path():
    with pytest.raises(FileNotFoundError):
        InvertedIndex.load("impresed")


# def test_callback_query()
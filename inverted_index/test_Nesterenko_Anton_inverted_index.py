import os
from argparse import Namespace
from textwrap import dedent

import pytest

from task_Nesterenko_Anton_inverted_index import InvertedIndex, load_documents, \
    build_inverted_index, StructStoragePolicy, callback_query, callback_build


DATASET_SMALL_STR = dedent("""\
    12\tAnarchism Anarchism is often defined as a political philosophy which holds the state to be undesirable.
    25\tAutism Autism is a disorder of neural development characterized by impaired social interaction
    39\tAlbedo Albedo, or reflection coefficient, derived from Latin albedo "whiteness" (or reflected sunlight)
    290\tA  A (named a  , plural aes ) is the first letter and vowel in the ISO basic Latin alphabet.
""")

DATASET_TINY_STR = dedent("""\
    123\tShow must go on!
    321\tStill loving you
    547\tThe Adventures of Rain Dance Maggie
    645\tThe House of Rising Son
    789\tA A B
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
    dataset_fio = tmpdir.join("tiny_dataset.txt")
    dataset_fio.write(DATASET_TINY_STR)
    return dataset_fio


@pytest.fixture()
def small_dataset_fio(tmpdir):
    dataset_fio = tmpdir.join("small_dataset.txt")
    dataset_fio.write(DATASET_TINY_STR)
    return dataset_fio


@pytest.mark.parametrize(
    "dataset, length",
    [
        pytest.param(DATASET_TINY_STR, 5),
        pytest.param(DATASET_SMALL_STR, 4),
    ]
)
def test_can_run_load_documents(tmpdir, dataset,  length):
    datapath = tmpdir.join("dataset.txt")
    datapath.write(dataset)
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
    "dataset",
    [
        DATASET_TINY_STR,
        DATASET_SMALL_STR
    ]
)
def test_can_run_build_index(tmpdir, dataset):
    datapath = tmpdir.join("dataset.txt")
    datapath.write(dataset)
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
    inverted_index.dump(StructStoragePolicy(), tmp_fio)
    assert os.path.isfile(tmp_fio), "File was not created"


def test_inverted_index_can_dump_load_index(tmpdir):
    datapath = tmpdir.join("dataset.txt")
    datapath.write(DATASET_SMALL_STR)
    documents = load_documents(datapath)
    inverted_index = build_inverted_index(documents)
    tmp_fio = tmpdir.join('test.dump')
    inverted_index.dump(StructStoragePolicy(), tmp_fio)
    loaded_index = inverted_index.load(StructStoragePolicy(), tmp_fio)
    assert inverted_index._index == loaded_index._index, "File was not created"


def test_inverted_index_load_wrong_path():
    with pytest.raises(FileNotFoundError):
        InvertedIndex.load(StructStoragePolicy(), "impresed")


@pytest.mark.parametrize(
    "query, answer",
    [
        pytest.param(["Show"], {123}),
        pytest.param(["The"], {547, 645}),
        pytest.param(["The", "Adventures"], {547}),
        pytest.param(["Unforgiven"], set()),
    ]
)
def test_callback_query_list(tiny_dataset_fio, tmpdir, capsys, query, answer):
    documents = load_documents(tiny_dataset_fio)
    inverted_index = build_inverted_index(documents)
    tmp_fio = tmpdir.join('test.dump')
    inverted_index.dump(StructStoragePolicy(), tmp_fio)
    arguments = Namespace(
        query=query,
        index_path=tmp_fio
    )
    callback_query(arguments)
    captured = capsys.readouterr()
    if captured.out == "\n":
        query_ans = set()
    else:
        query_ans = set(int(var) for var in captured.out.rstrip().split(","))
    assert query_ans == answer, "Wrong answer"


@pytest.mark.parametrize(
    "query, answer",
    [
        pytest.param(["Show"], {123}),
        pytest.param(["The"], {547, 645}),
        pytest.param(["The", "Adventures"], {547}),
        pytest.param(["Русский"], set()),
    ]
)
def test_callback_query_utf8(tiny_dataset_fio, tmpdir, capsys, query, answer):
    documents = load_documents(tiny_dataset_fio)
    inverted_index = build_inverted_index(documents)
    tmp_fio = tmpdir.join('test.dump')
    inverted_index.dump(StructStoragePolicy(), tmp_fio)
    tmp_file = tmpdir.join('test.utf8')
    with open(tmp_file, "w", encoding="utf8") as file:
        file.write(" ".join(query) + "\n")
    arguments = Namespace(
        query=[],
        query_file=open(tmp_file, "r", encoding="utf8"),
        index_path=tmp_fio
    )
    callback_query(arguments)
    captured = capsys.readouterr()
    if captured.out == "\n":
        query_ans = set()
    else:
        query_ans = set(int(var) for var in captured.out.rstrip().split(","))
    assert query_ans == answer, "Wrong answer"


@pytest.mark.parametrize(
    "query, answer",
    [
        pytest.param(["Show"], {123}),
        pytest.param(["The"], {547, 645}),
        pytest.param(["The", "Adventures"], {547}),
        pytest.param(["Русский"], set()),
    ]
)
def test_callback_query_cp1251(tiny_dataset_fio, tmpdir, capsys, query, answer):
    documents = load_documents(tiny_dataset_fio)
    inverted_index = build_inverted_index(documents)
    tmp_fio = tmpdir.join('test.dump')
    inverted_index.dump(StructStoragePolicy(), tmp_fio)
    tmp_file = tmpdir.join('test.cp1251')
    with open(tmp_file, "w", encoding="cp1251") as file:
        file.write(" ".join(query) + "\n")
    arguments = Namespace(
        query=[],
        query_file=open(tmp_file, "r", encoding="cp1251"),
        index_path=tmp_fio
    )
    callback_query(arguments)
    captured = capsys.readouterr()
    if captured.out == "\n":
        query_ans = set()
    else:
        query_ans = set(int(var) for var in captured.out.rstrip().split(","))
    assert query_ans == answer, "Wrong answer"


def test_callback_build(tmpdir):
    datapath = tmpdir.join("dataset.txt")
    datapath.write(DATASET_SMALL_STR)
    tmp_fio = tmpdir.join('test.dump')
    arguments = Namespace(
        load_path=datapath,
        store_path=tmp_fio
    )
    callback_build(arguments)
    assert os.path.isfile(tmp_fio), "Index was not created"

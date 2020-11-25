"""
Module for inverted index, library for efficient word search in documents
"""

import argparse
import io
import os
import sys
import struct
from abc import ABC
from collections import defaultdict
from typing import Dict, List


class EncodedFileType(argparse.FileType):
    """
    Class to fix encoding error from buffer read
    """

    def __call__(self, string):
        if string == '-':
            if 'r' in self._mode:
                stdin = io.TextIOWrapper(sys.stdin, encoding=self._encoding)
                return stdin
            elif 'w' in self._mode:
                stdout = io.TextIOWrapper(sys.stdin, encoding=self._encoding)
                return stdout
            else:
                msg = 'argument "-" with mode %r' % self._mode
                raise ValueError(msg)

        # all other arguments are used as file names
        try:
            return open(string, self._mode, self._bufsize, self._encoding,
                        self._errors)
        except OSError as exception:
            args = {'filename': string, 'error': exception}
            message = "can't open '%(filename)s': %(error)s"
            raise argparse.ArgumentTypeError(message % args)


class StoragePolicy(ABC):

    """
    Abstract class for save load document policy
    """

    @staticmethod
    def dump(filepath: str, index: Dict[str, List[int]]):
        """Abstract method for saving document
        :param filepath: path to save a data
        :param index: index dict in format word: [doc1, doc2, docN]
        :return: Nothing
        """

    @staticmethod
    def load(filepath: str) -> Dict[str, List[int]]:
        """
        Abstract method for loading index from disc
        :param filepath: path to file
        :return: index dict in format word: [doc1, doc2, docN]
        """


class StructStoragePolicy(StoragePolicy):
    """
    Struct storage policy for size efficient storing data on disc
    """
    @staticmethod
    def dump(filepath: str, index: Dict[str, List[int]]):
        """
        Save given index dict in decoded format
        :param filepath: path to save a data
        :param index: index dict in format word: [doc1, doc2, docN]
        :return: Nothing
        """
        max_value = max([max(v) for v in index.values()])
        value_fmt = "H" if max_value < 65535 else "I"
        with open(filepath, 'wb') as fio:
            fio.write(struct.pack("I", max_value))
            for key, value in index.items():
                key_bytes = key.encode('utf8')
                fio.write(struct.pack(">H", len(key_bytes)))
                fio.write(key_bytes)
                fio.write(struct.pack(">" + value_fmt, len(value)))
                fio.write(struct.pack(">" + value_fmt * len(value), *value))

    @staticmethod
    def load(filepath: str) -> Dict[str, List[int]]:
        """Upload index from disc and decode it
        :param filepath: path to file with data
        :return: ndex dict in format word: [doc1, doc2, docN]"""
        index = {}
        with open(filepath, 'rb') as fio:
            file_size = os.fstat(fio.fileno()).st_size
            max_value, = struct.unpack("I", fio.read(4))
            file_size -= 4
            value_fmt = "H" if max_value < 65535 else "I"
            value_size = 2 if max_value < 65535 else 4
            while file_size > 0:
                bytes_len, = struct.unpack(">H", fio.read(2))
                file_size -= 2
                key = fio.read(bytes_len).decode("utf8")
                file_size -= bytes_len
                values_len, = struct.unpack(">" + value_fmt, fio.read(value_size))
                file_size -= value_size
                values = list(struct.unpack(">" + value_fmt * values_len, fio.read(values_len * value_size)))
                file_size -= values_len * value_size
                index[key] = values
        return index


class InvertedIndex:
    """
    Inverted Index class for fast search words in documents.
    Provides search, load and save interface
    """
    def __init__(self, index: Dict[str, List[int]]) -> None:
        """
        Class construction method
        :param index: dict of loaded documents converted to format: word: [doc1, doc2, docN]
        :return Nothing
        """
        self._index = index

    def query(self, words: List[str]) -> List[int]:
        """Return the list of relevant documents for the given query
        :param words: list of words for search
        :return documents where all of words are presented together
        """
        tmp = None
        for word in words:
            if word in self._index:
                if tmp is None:
                    tmp = set(self._index[word])
                else:
                    tmp.intersection_update(set(self._index[word]))
            else:
                return list()
        return list(tmp)

    def dump(self, policy: StoragePolicy, filepath: str) -> None:
        """
        Save class index on disc by given path
        :param policy: policy for data dump
        :param filepath: path to save a data
        :return: Nothing
        """
        policy.dump(filepath, self._index)

    @classmethod
    def load(cls, policy: StoragePolicy, filepath: str):
        """
        Upload index from disc and construct InvertedIndex class
        :param policy: policy for data load
        :param filepath: path to file with data
        :return: Class built by data in given filename
        """
        index = policy.load(filepath)
        return InvertedIndex(index)


def load_documents(filepath: str):
    """
    Function for loading documents from disc
    :param filepath: path to file with document with format "id[\\s]text"
    :return: dict of documents in format id: text
    """
    documents = {}
    with open(filepath, 'r') as fin:
        for row in fin:
            row = row.strip().split()
            documents[int(row[0])] = " ".join(row[1:])
    return documents


def build_inverted_index(documents: Dict[int, str]) -> InvertedIndex:
    """
    Build inverted index from given dict of documents
    :param documents: dict of documents in format id: text
    :return: built InvertedIndex class
    """
    index = defaultdict(set)
    for doc_id, doc_text in documents.items():
        for word in doc_text.split():
            index[word].add(doc_id)
    index = {k: list(v) for k, v in index.items()}
    return InvertedIndex(index)


def callback_build(arguments):
    """
    Callback function for build command
    :param arguments: command line arguments
    :return: Nothing
    """
    documents = load_documents(arguments.load_path)
    inverted_index = build_inverted_index(documents)
    inverted_index.dump(StructStoragePolicy(), arguments.store_path)


def callback_query(arguments):
    """
    Callback function for query command
    :param arguments: command line arguments
    :return: Nothing
    """
    inverted_index = InvertedIndex.load(StructStoragePolicy(), arguments.index_path)
    if arguments.query:
        print(",".join([str(var) for var in inverted_index.query(arguments.query)]))
    else:
        for row in arguments.query_file:
            print(",".join([str(var) for var in inverted_index.query(row.strip().split())]))


def setup_parser(parser: argparse.ArgumentParser) -> None:
    """
    Function for setup command line parser arguments
    :param parser: parser for arguments
    :return: Nothing
    """
    subparsers = parser.add_subparsers(help="choose command")
    build_parser = subparsers.add_parser("build",
                                         help="build inverted index from data and save it to disc")
    query_parser = subparsers.add_parser("query",
                                         help="query inverted index from disc and return documents")
    build_parser.add_argument("--dataset", dest="load_path",
                              help="path to documents to collect inverted index", required=True)
    build_parser.add_argument("--output", dest="store_path",
                              help="path to store builded inverted index", required=True)
    build_parser.set_defaults(callback=callback_build)
    query_parser.add_argument("--index", dest="index_path",
                              help="path to saved inverted index", required=True)
    query_group = query_parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument("--query", help="word to run query against", nargs="+")
    query_group.add_argument("--query-file-utf8", help="", dest="query_file",
                             type=EncodedFileType("r", encoding="utf-8"),
                             default=io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8"))
    query_group.add_argument("--query-file-cp1251", help="", dest="query_file",
                             type=EncodedFileType("r", encoding="cp1251"),
                             default=io.TextIOWrapper(sys.stdin.buffer, encoding="cp1251"))
    query_parser.set_defaults(callback=callback_query)


def main():
    parser = argparse.ArgumentParser(
        prog="inverted_index",
        description="tool to build, save, load and query inverted index"
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)


if __name__ == "__main__":
    main()

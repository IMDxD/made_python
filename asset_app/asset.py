#!/usr/bin/env python3
"""
Web service for asset application
"""

import logging
import requests
from typing import Dict

from bs4 import BeautifulSoup
from flask import Flask, Response, make_response, jsonify


DAILY_URL = "https://www.cbr.ru/eng/currency_base/daily/"
INTEREST_KEY_URL = "https://www.cbr.ru/eng/key-indicators/"


logger = logging.getLogger("asset")
app = Flask(__name__)


class Asset:
    """
    Class for client asset
    """
    def __init__(self, name: str, capital: float, interest: float):
        """
        Class initialization
        :param name: client name
        :param capital: client capital
        :param interest: interest rate for client
        """
        self.name = name
        self.capital = capital
        self.interest = interest

    def calculate_revenue(self, years: int) -> float:
        """
        Calculate revenue by given period
        :param years: period for calc
        :return: revenue of asset by given period
        """
        revenue = self.capital * ((1.0 + self.interest) ** years - 1.0)
        return revenue

    @classmethod
    def build_from_str(cls, raw: str):
        """
        Create Asset class from string
        :param raw: Asset row
        :return: built class
        """
        name, capital, interest = raw.strip().split()
        capital = float(capital)
        interest = float(interest)
        asset = cls(name=name, capital=capital, interest=interest)
        return asset

    def __repr__(self):
        """
        Text representation of class
        :return: text representation
        """
        repr_ = f"{self.__class__.__name__}({self.name}, {self.capital}, {self.interest})"
        return repr_


@app.errorhandler(404)
def page_not_found(e) -> Response:
    """
    Default 404 error
    :return: response for 404 page
    """
    return make_response("This route is not found", 404)


def cbr_float(string: str) -> float:
    """
    Convert string from cbr.ru to float
    :param string: string to convert
    :return: float
    """
    return float(string.replace(",", ""))


def parse_cbr_currency_base_daily(html: str) -> Dict[str, float]:
    """
    Parse https://www.cbr.ru/eng/currency_base/daily/
    and return mapping of char code to 1 unit price
    :param html: page content
    :return: mapping of char code to 1 unit price
    """
    result = dict()
    parsed = BeautifulSoup(html, "html.parser")
    table = parsed.find("table", attrs={"class": "data"})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 5:
            result[cols[1].text] = cbr_float(cols[4].text) / cbr_float(cols[2].text)
    return result


def parse_cbr_key_indicators(html: str) -> Dict[str, float]:
    """
    Parse https://www.cbr.ru/eng/currency_base/daily/
    and return mapping of char code to 1 unit price
    :param html: page content
    :return: mapping of char code to 1 unit price
    """
    result = dict()
    parsed = BeautifulSoup(html, "html.parser")
    div_tables = parsed.find_all("div", attrs={"class": "table key-indicator_table"})
    for div_table in div_tables[:2]:
        rows = div_table.findAll("tr")
        for row in rows[1:]:
            char_code = row.find("div",
                                 attrs={"class": "col-md-3 offset-md-1 _subinfo"}).text
            value = cbr_float(row.findAll("td")[-1].text)
            result[char_code] = value
    return result


@app.route("/cbr/daily")
def cbr_daily_api() -> Response:
    """
    Api method for getting currency mapping from
    https://www.cbr.ru/eng/currency_base/daily/
    :return: Json with parsed data
    """
    response = requests.get(DAILY_URL)
    if response.status_code == 503:
        return make_response("CBR service is unavailable", 503)
    else:
        result = parse_cbr_currency_base_daily(response.text)
        return jsonify(result)


@app.route("/cbr/key_indicators")
def cbr_interest_key_api() -> Response:
    """
    Api method for getting currency mapping from
    https://www.cbr.ru/eng/currency_base/daily/
    :return: Json with parsed data
    """
    response = requests.get(INTEREST_KEY_URL)
    if response.status_code == 503:
        return make_response("CBR service is unavailable", 503)
    else:
        result = parse_cbr_key_indicators(response.text)
        return jsonify(result)

#!/usr/bin/env python3
"""
Web service for asset application
"""
import logging
from collections import defaultdict
from typing import Any, Dict, List, Union

import requests
from bs4 import BeautifulSoup
from flask import Flask, Response, jsonify, make_response, request

DAILY_URL = "https://www.cbr.ru/eng/currency_base/daily/"
INTEREST_KEY_URL = "https://www.cbr.ru/eng/key-indicators/"


class Asset:
    """
    Class for client asset
    """
    def __init__(self, name: str, capital: float, interest: float, char_code: str):
        """
        Class initialization
        :param name: client name
        :param capital: client capital
        :param interest: interest rate for client
        :param char_code: currency of asset
        """
        self.name = name
        self.capital = capital
        self.interest = interest
        self.char_code = char_code

    def calculate_revenue(self, years: int) -> float:
        """
        Calculate revenue by given period
        :param years: period for calc
        :return: revenue of asset by given period
        """
        revenue = self.capital * ((1 + self.interest / 100) ** years - 1.0)
        return revenue

    def __repr__(self):
        """
        Text representation of class
        :return: text representation
        """
        repr_ = f"{self.__class__.__name__}({self.name}, {self.capital}, {self.interest}, {self.char_code})"
        return repr_

    def __lt__(self, other) -> bool:
        """
        Operator < for class
        :param other: right value
        :return: comparision result
        """
        if isinstance(other, Asset):
            return self.name < other.name
        raise ValueError(f"Can't compare Asset and {other.__class__.__name__}")


class Bank:

    """Class for storing asset list"""

    def __init__(self, asset_list: Union[List[Asset], None] = None):
        """
        Bank constructor
        :param asset_list: list of assets or None
        """
        self.asset_list = list()
        if asset_list:
            self.asset_list.extend(asset_list)

    def add(self, item: Asset):
        """
        Add asset to bank
        :return: Nothing
        """
        self.asset_list.append(item)

    def contains(self, item: Asset) -> bool:
        """
        Check does item contains in list
        :param item: item to check
        :return: True if item contains else False
        """
        for asset in self.asset_list:
            if asset.name == item.name:
                return True
        return False

    def get_json(self) -> List[List[Any]]:
        """
        Return json repr of bank
        :return: list of repr
        """
        result = []
        for item in self.asset_list:
            result.append([item.char_code, item.name, str(item.capital), str(item.interest)])
        return result

    def clear(self):
        """
        Clear bank
        :return: Nothing
        """
        self.asset_list.clear()

    def get(self, name: str) -> List[Any]:
        """
        Method to get asset list repr by name
        :param name: name of asset
        :return: list repr
        """
        for item in self.asset_list:
            if item.name == name:
                return [item.char_code, item.name, item.capital, item.interest]
        return []

    def total_revenue(self, period: int,
                      key_interest_map: Dict[str, float],
                      daily_map: Dict[str, float]) -> float:
        """
        Function to calculate total revenue by given mapping of key_interest and daily map
        :param period: period for revenue
        :param key_interest_map: mapping of char code to currency value
        :param daily_map: mapping of char code to currency value
        :return: Total revenue of bank
        """
        result = 0
        for item in self.asset_list:
            if item.char_code in key_interest_map:
                mapping = key_interest_map[item.char_code]
            else:
                mapping = daily_map[item.char_code]
            result += item.calculate_revenue(period) * mapping
        return result


logger = logging.getLogger("asset")
app = Flask(__name__)
app.bank = Bank()


@app.errorhandler(404)
def page_not_found(e) -> Response:
    """
    Default 404 error
    :return: response for 404 page
    """
    return make_response("This route is not found", 404)


@app.errorhandler(500)
def cbr_unavailable_found(e) -> Response:
    """
    Default 404 error
    :return: response for 404 page
    """
    return make_response("CBR service is unavailable", 503)


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
    result = parse_cbr_key_indicators(response.text)
    return jsonify(result)


@app.route("/api/asset/add/<string:char_code>/<string:name>/<int:capital>/<int:interest>")
def add_asset_api(char_code: str, name: str, capital: int, interest: int) -> Response:
    """
    Api to add asset
    :param char_code: char code of asset
    :param name: name of asset
    :param capital: capital of asset
    :param interest: interest of asset
    :return: 200 if asset not exist else 403
    """
    new_asset = Asset(
        name=name,
        capital=capital,
        interest=interest,
        char_code=char_code
    )
    if app.bank.contains(new_asset):
        return make_response("Name has already exist", 403)
    app.bank.add(new_asset)
    return make_response(f"Asset '{name}' was successfully added", 200)


@app.route("/asset/cleanup")
def clear_api():
    """
    Api for bank cleanup
    :return: Response 200
    """
    app.bank.clear()
    return make_response("Successfully cleared", 200)


@app.route("/api/asset/list")
def asset_list_api():
    """
    Api to get bank asset list
    :return: json of bank asset list
    """
    data = app.bank.get_json()
    return jsonify(data)


@app.route("/api/asset/get")
def asset_get_api():
    """
    Api to get asset from bank list by names
    :return: json of bank asset list
    """
    data = []
    names = request.args.getlist('name')
    for name in names:
        asset = app.bank.get(name)
        if asset:
            data.append(asset)
    return jsonify(data)


@app.route("/api/asset/calculate_revenue")
def asset_calc_revenue_api():
    """
    Api to calculate revenue by given periods
    :return: json of dict period to revenue
    """
    data = defaultdict(str)
    periods = request.args.getlist('period')
    cbr_interest_response = requests.get(INTEREST_KEY_URL)
    cbr_daily_response = requests.get(DAILY_URL)
    interest_map = parse_cbr_key_indicators(cbr_interest_response.text)
    daily_map = parse_cbr_currency_base_daily(cbr_daily_response.text)
    for period in periods:
        data[period] = str(
            app.bank.total_revenue(
                period=int(period),
                key_interest_map=interest_map,
                daily_map=daily_map)
        )
    return jsonify(data)

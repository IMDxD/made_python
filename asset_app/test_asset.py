import pytest
from unittest.mock import patch
from asset import Asset, DAILY_URL, INTEREST_KEY_URL, app as test_app, cbr_float, \
    parse_cbr_currency_base_daily, parse_cbr_key_indicators


@pytest.fixture
def client():
    with test_app.test_client() as client:
        yield client


def test_asset_init():
    new_asset = Asset("Vasya", 12.0, 123)
    assert new_asset.name == "Vasya" and new_asset.capital == 12.0 \
           and new_asset.interest == 123, "Wrong asset init"


@pytest.mark.parametrize(
    "years, result",
    [
        pytest.param(1, 12 * ((1.0 + 0.5) ** 1 - 1.0)),
        pytest.param(5, 12 * ((1.0 + 0.5) ** 5 - 1.0)),
        pytest.param(10, 12 * ((1.0 + 0.5) ** 10 - 1.0))
    ]
)
def test_asset_calc_revenue(years, result):
    new_asset = Asset("Vasya", 12.0, 0.5)
    calced_revenue = new_asset.calculate_revenue(years)
    assert calced_revenue == result, f"Wrong revenue expected {calced_revenue:.3f}, " \
                                     f"get {result:.3f}"


def test_asset_repr():
    new_asset = Asset("Vasya", 12.0, 0.5)
    assert repr(new_asset) == "Asset(Vasya, 12.0, 0.5)", \
        f"Wrong repr: {repr(new_asset)}, expected Asset(Vasya, 12.0, 0.5)"


@pytest.mark.parametrize(
    "string, result",
    [
        pytest.param("Petya 12 1", Asset("Petya", 12, 1)),
        pytest.param("Vasya -8.0 3", Asset("Vasya", -8.0, 3)),
        pytest.param("Masha 0 0", Asset("Masha", 0, 0))
    ]
)
def test_asset_build_from_str(string, result):
    new_asset = Asset.build_from_str(string)
    assert new_asset.name == result.name and \
           new_asset.capital == result.capital and \
           new_asset.interest == result.interest, \
           f"Wrong asset created got {new_asset}, expected {result}"


def test_cbr_float():
    expected = 5256.23
    result = cbr_float("5,256.23")
    assert expected == result, f"Wrong answer expected {expected}, got {result}"


def test_default_not_exist(client):
    expected = "This route is not found"
    result = client.get("/random_url")
    assert 404 == result.status_code, \
        f"Wrong status_code expected: 404, got: {result.status_code}"
    assert expected == result.data.decode(), \
        f"Wrong message expected: {expected}, got: {result.data.decode()}"


def test_parse_cbr_currency_base_daily():
    expected_result = {
        "AUD": 57.0229,
        "AZN": 44.4127,
        "AMD": 0.144485
    }
    with open("test_data/cbr_daily.html", "r", encoding="utf8") as fs:
        result = parse_cbr_currency_base_daily(fs.read())
    assert result == expected_result, f"Wrong result expected: {expected_result}, got: {result}"


def test_parse_cbr_key_indicators():
    expected_result = {
        "USD": 75.4571,
        "EUR": 91.9822,
        "Au": 4529.59,
        "Ag": 62.52,
        "Pt": 2459.96,
        "Pd": 5667.14
    }
    with open("test_data/cbr_indicator.html", "r", encoding="utf8") as fs:
        result = parse_cbr_key_indicators(fs.read())
    assert result == expected_result, f"Wrong result expected: {expected_result}, got: {result}"


@patch("requests.get")
def test_cbr_daily_api(mock_get, client):
    with open("test_data/cbr_daily.html", "r", encoding="utf8") as fs:
        mock_get.return_value.text = fs.read()
    expected = {
        "AUD": 57.0229,
        "AZN": 44.4127,
        "AMD": 0.144485
    }
    result = client.get("/cbr/daily")
    mock_get.called_once(DAILY_URL)
    assert expected == result.json, f"Wrong result expected: {expected}, got: {result}"


@patch("requests.get")
def test_cbr_daily_api_unavailable(mock_get, client):
    mock_get.return_value.status_code = 503
    expected = "CBR service is unavailable"
    result = client.get("/cbr/daily")
    mock_get.called_once(DAILY_URL)
    assert 503 == result.status_code, f"Wrong status_code expected: 503, got: {result.status_code}"
    assert expected == result.data.decode(), \
        f"Wrong message expected: {expected}, got: {result.data.decode()}"


@patch("requests.get")
def test_cbr_key_indicator_api(mock_get, client):
    with open("test_data/cbr_indicator.html", "r", encoding="utf8") as fs:
        mock_get.return_value.text = fs.read()
    expected = {
        "USD": 75.4571,
        "EUR": 91.9822,
        "Au": 4529.59,
        "Ag": 62.52,
        "Pt": 2459.96,
        "Pd": 5667.14
    }
    result = client.get("/cbr/key_indicators")
    mock_get.called_once(INTEREST_KEY_URL)
    assert expected == result.json, f"Wrong result expected: {expected}, got: {result}"


@patch("requests.get")
def test_cbr_key_indicator_api_unavailable(mock_get, client):
    mock_get.return_value.status_code = 503
    expected = "CBR service is unavailable"
    result = client.get("/cbr/key_indicators")
    mock_get.called_once(INTEREST_KEY_URL)
    assert 503 == result.status_code, f"Wrong status_code expected: 503, got: {result.status_code}"
    assert expected == result.data.decode(), \
        f"Wrong message expected: {expected}, got: {result.data.decode()}"
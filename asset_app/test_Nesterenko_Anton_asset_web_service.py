import pytest
from unittest.mock import patch
from collections import defaultdict, namedtuple
from task_Nesterenko_Anton_asset_web_service import \
    Asset, Bank, DAILY_URL, INTEREST_KEY_URL, app as test_app, cbr_float, \
    parse_cbr_currency_base_daily, parse_cbr_key_indicators


@pytest.fixture
def client():
    with test_app.test_client() as client:
        yield client


def test_asset_init():
    new_asset = Asset("Vasya", 12.0, 123, "USD")
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
    new_asset = Asset("Vasya", 12.0, 0.5, "USD")
    calced_revenue = new_asset.calculate_revenue(years)
    assert calced_revenue == result, f"Wrong revenue expected {calced_revenue:.3f}, " \
                                     f"get {result:.3f}"


@pytest.mark.parametrize(
    "left, right, result",
    [
        pytest.param(Asset("Vasya", 12, 12, "USD"), Asset("Petya", 32, 1, "EU"), False),
        pytest.param(Asset("Vasya", 12, 12, "USD"), Asset("Vasya", 32, 1, "USA"), False),
        pytest.param(Asset("Petya", 12, 12, "RUB"), Asset("Vasya", 32, 1, "ARM"), True)
    ]
)
def test_asset_comp(left, right, result):
    assert (left < right) is result, f"Wrong comp: left {left.name}, right {right.name}" \
                                     f"got {left < right}"


def test_asset_error():
    left = Asset("Vasya", 12, 12, "USD")
    with pytest.raises(ValueError):
        left < "123"


def test_asset_repr():
    new_asset = Asset("Vasya", 12.0, 0.5, "USD")
    assert repr(new_asset) == "Asset(Vasya, 12.0, 0.5, USD)", \
        f"Wrong repr: {repr(new_asset)}, expected Asset(Vasya, 12.0, 0.5)"


@pytest.mark.parametrize(
    "data, result",
    [
        pytest.param([Asset("Vasya", 12, 12, "USD"),
                      Asset("Petya", 32, 1, "USD"),
                      Asset("Masha", 0, 0, "USD")],
                     ["Vasya", "Petya", "Masha"]),
        pytest.param(None, [])
    ]
)
def test_bank_init(data, result):
    bank = Bank(data)
    bank_names = [var.name for var in bank.asset_list]
    assert bank_names == result, f"Wrong result got: {bank_names}, expect: {result}"


def test_bank_append():
    item = Asset("Vasya", 12, 12, "USD")
    asset1 = Asset("Petya", 12, 12, "USD")
    asset2 = Asset("Masha", 0, 0, "USD")
    expected = ["Petya", "Masha", "Vasya"]
    bank = Bank([asset1, asset2])
    bank.add(item)
    bank_names = [var.name for var in bank.asset_list]
    assert bank_names == expected, f"Wrong result got: {bank_names}, expect: {expected}"


@pytest.mark.parametrize(
    "item, result",
    [
        pytest.param(Asset("Vasya", 12, 12, "USD"), False),
        pytest.param(Asset("Petya", 12, 12, "USD"), True)
    ]
)
def test_bank_contains(item, result):
    asset1 = Asset("Petya", 12, 12, "USD")
    asset2 = Asset("Masha", 0, 0, "USD")
    bank = Bank([asset1, asset2])
    cont = bank.contains(item)
    assert cont == result, f"Wrong result got: {cont}, expect: {result}"


def test_bank_clear():
    asset1 = Asset("Petya", 12, 12, "USD")
    asset2 = Asset("Masha", 0, 0, "USD")
    bank = Bank([asset1, asset2])
    bank.clear()
    assert len(bank.asset_list) == 0, f"Wrong result got: {len(bank.asset_list)}, expect: 0"


def test_bank_get():
    asset1 = Asset("Petya", 12, 12, "USD")
    asset2 = Asset("Masha", 0, 5, "USD")
    bank = Bank([asset1, asset2])
    res = bank.get("Masha")
    expected = ["USD", "Masha", 0, 5]
    assert res == expected, f"Wrong result got: {res}, expect: {expected}"


def test_bank_get_json():
    asset1 = Asset("Petya", 12, 13, "USD")
    asset2 = Asset("Masha", 0, 1, "EU")
    result = [
        ["USD", "Petya", "12", "13"],
        ["EU", "Masha", "0", "1"]
    ]
    bank = Bank([asset1, asset2])
    gotten = bank.get_json()
    assert gotten == result, f"Wrong result got: {gotten}, expect: {result}"


def test_bank_total_revenue():
    asset1 = Asset("Petya", 12, 13, "USD")
    asset2 = Asset("Masha", 0, 1, "EU")
    asset3 = Asset("Vasya", 50, 61, "ARM")
    asset4 = Asset("Lesha", 50, 61, "AU")
    key_map = {
        "EU": 90,
        "USD": 72.5,
    }
    daily_map = {
        "ARM": 0.1,
        "AU": 40.5
    }
    period = 5
    result = asset1.calculate_revenue(period) * 72.5
    result += asset2.calculate_revenue(period) * 90
    result += asset3.calculate_revenue(period) * 0.1
    result += asset4.calculate_revenue(period) * 40.5
    bank = Bank([asset1, asset2, asset3, asset4])
    gotten = bank.total_revenue(period, key_map, daily_map)
    assert gotten == result, f"Wrong result got: {gotten}, expect: {result}"


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


@pytest.mark.parametrize(
    "route, result, length",
    [
        pytest.param("/api/asset/add/EU/Vasya/12/12", ("Vasya", 12, 12, "EU"), 1),
        pytest.param("/api/asset/add/USD/Masha/1/1", ("Masha", 1, 1, "USD"), 2)
    ]
)
def test_add_asset_api(route, result, length, client):
    response = client.get(route)
    asset = (
        client.application.bank.asset_list[-1].name,
        client.application.bank.asset_list[-1].capital,
        client.application.bank.asset_list[-1].interest,
        client.application.bank.asset_list[-1].char_code
    )
    banks_cnt = len(client.application.bank.asset_list)
    message = f"Asset '{asset[0]}' was successfully added"
    assert response.status_code == 200, f"Wrong status code, expected 200, got {response.status_code}"
    assert response.data.decode() == message, f"Wrong message, expected {message}, got {result.data.decode()}"
    assert asset == result, f"Wrong result expected: {result}, got: {asset}"
    assert banks_cnt == length, f"Wrong bank count, expected {length}, got {banks_cnt}"


def test_api_clear(client):
    client.application.bank = Bank([
        Asset("Petya", 12, 13, "USD"),
        Asset("Masha", 0, 1, "EU")
    ])
    response = client.get("/asset/cleanup")
    message = "Successfully cleared"
    banks_cnt = len(client.application.bank.asset_list)
    assert response.status_code == 200, f"Wrong status code, expected 200, got {response.status_code}"
    assert response.data.decode() == message, f"Wrong message, expected {message}, got {response.data.decode()}"
    assert banks_cnt == 0, f"Wrong bank count, expected 0, got {banks_cnt}"


def test_add_asset_api_contains(client):
    client.application.bank = Bank()
    client.get("/api/asset/add/EU/Vasya/12/12")
    response = client.get("/api/asset/add/EU/Vasya/12/12")
    banks_cnt = len(client.application.bank.asset_list)
    assert response.status_code == 403, f"Wrong status code, expected 200, got {response.status_code}"
    assert banks_cnt == 1, f"Wrong bank count, expected 1, got {banks_cnt}"


def test_api_asset_list(client):
    client.application.bank = Bank([
        Asset("Petya", 12, 13, "USD"),
        Asset("Masha", 0, 1, "EU")
    ])
    result = [
        ["USD", "Petya", "12", "13"],
        ["EU", "Masha", "0", "1"]
    ]
    response = client.get("/api/asset/list")
    assert response.json == result,  f"Wrong result expected: {result}, got: {response.json}"
    assert response.status_code == 200, f"Wrong status code, expected 200, got {response.status_code}"


@pytest.mark.parametrize(
    "route, result",
    [
        pytest.param("/api/asset/get?name=Vasya&name=Masha",
                     [
                         ["ARM", "Vasya", 50, 61],
                         ["EU", "Masha", 0, 1]
                     ]
                     ),
        pytest.param("/api/asset/get?name=Petya",
                     [
                         ["USD", "Petya", 12, 13],
                     ]
                     ),
    ]
)
def test_api_asset_get(route, result, client):
    client.application.bank = Bank([
        Asset("Petya", 12, 13, "USD"),
        Asset("Masha", 0, 1, "EU"),
        Asset("Vasya", 50, 61, "ARM"),
        Asset("Lesha", 50, 61, "AU"),
    ])

    response = client.get(route)
    assert response.json == result,  f"Wrong result expected: {result}, got: {response.json}"
    assert response.status_code == 200, f"Wrong status code, expected 200, got {response.status_code}"


@patch("requests.get")
@pytest.mark.parametrize(
    "route, periods",
    [
        pytest.param("/api/asset/calculate_revenue?period=3", [3]),
        pytest.param("/api/asset/calculate_revenue?period=3&period=5", [3, 5])
    ]
)
def test_calculate_revenue_api(mock_get, route, periods, client):
    side_effect = []
    return_value = namedtuple("return_value", ["text"])
    with open("test_data/cbr_indicator.html", "r", encoding="utf8") as fs:
        side_effect.append(return_value(fs.read(),))
    with open("test_data/cbr_daily.html", "r", encoding="utf8") as fs:
        side_effect.append(return_value(fs.read(),))
    mock_get.side_effect = side_effect
    daily = {
        "AUD": 57.0229,
        "AZN": 44.4127,
        "AMD": 0.144485
    }
    interest = {
        "USD": 75.4571,
        "EUR": 91.9822,
        "Au": 4529.59,
        "Ag": 62.52,
        "Pt": 2459.96,
        "Pd": 5667.14
    }
    client.application.bank = Bank([
        Asset("Petya", 12, 13, "USD"),
        Asset("Masha", 0, 1, "Au"),
        Asset("Vasya", 2, 43, "AZN"),
        Asset("Lesha", 50, 61, "AMD"),
    ])
    result = defaultdict(str)
    for period in periods:
        result[str(period)] = str(client.application.bank.total_revenue(period, interest, daily))
    response = client.get(route)
    mock_get.called_once(INTEREST_KEY_URL)
    mock_get.called_once(DAILY_URL)
    result = dict(result)
    assert response.json == result, f"Wrong result expected: {result}, got: {response.json}"
    assert response.status_code == 200, f"Wrong status code, expected 200, got: {response.status_code}"


@patch("requests.get")
def test_calculate_revenue_api_unavailable(mock_get, client):
    mock_get.return_value.status_code = 503
    expected = "CBR service is unavailable"
    result = client.get("/cbr/key_indicators")
    mock_get.called_once(INTEREST_KEY_URL)
    mock_get.called_once(DAILY_URL)
    assert 503 == result.status_code, f"Wrong status_code expected: 503, got: {result.status_code}"
    assert expected == result.data.decode(), \
        f"Wrong message expected: {expected}, got: {result.data.decode()}"

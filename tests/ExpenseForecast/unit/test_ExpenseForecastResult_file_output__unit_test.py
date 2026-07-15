from expense_forecast.ExpenseForecastResult import ExpenseForecastResult


def _result_with_stub_json():
    result = ExpenseForecastResult.__new__(ExpenseForecastResult)
    result.unique_id = "example"
    result.to_json_string = lambda: '{"result": true}'
    return result


def test_write_to_json_file_uses_supplied_path_as_file(tmp_path):
    result = _result_with_stub_json()
    output_path = tmp_path / "custom.json"

    assert result.writeToJSONFile(output_path) is True

    assert output_path.read_text() == '{"result": true}'
    assert not output_path.is_dir()


def test_write_to_json_file_uses_generated_name_when_path_is_omitted(
    tmp_path, monkeypatch
):
    result = _result_with_stub_json()
    monkeypatch.chdir(tmp_path)

    assert result.writeToJSONFile() is True

    assert (tmp_path / "Forecast_example.json").read_text() == '{"result": true}'

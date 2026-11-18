import pytest
import re

@pytest.fixture
def regex():
    return r"(?P<region>[^:]+):(?P<start>\d+)-(?P<end>\d+):?(?P<strand>[+-])?"

def generate_location(region, start, end, strand=None):
    strand_part = f":{strand}" if strand else ""
    return f"{region}:{start}-{end}{strand_part}"

@pytest.mark.parametrize("region, start, end, strand", [
    ("chr1", "12345", "67890", "+"),
    ("chr1", "12345", "67890", "-"),
    ("chr1", "12345", "67890", None),
])
def test_location_regex(regex, region, start, end, strand):
    location = generate_location(region, start, end, strand)
    match = re.match(regex, location)
    
    assert match is not None
    assert match.group("region") == region
    assert match.group("start") == start
    assert match.group("end") == end
    assert match.group("strand") == strand


@pytest.fixture
def location_config():
    import json
    from pathlib import Path
    config = json.loads((Path(__file__).resolve().parents[2] /
                         "datasets/genes/config/config.json").read_text())
    return next(f for f in config["filters"] if f["id"] == "location")


@pytest.mark.parametrize("problem", ["pattern", "fields", "groups", "operator"])
def test_etl_rejects_invalid_regex_configuration(location_config, problem):
    from pydantic import ValidationError
    from etl.models import Filter

    if problem == "pattern":
        location_config["regex"] = "["
    elif problem == "fields":
        location_config["extras"]["fields"] = []
    elif problem == "groups":
        location_config["extras"]["fields"][0]["regex_name"] = "missing"
    else:
        location_config["extras"]["fields"][0]["match"] = "= 1; DROP TABLE genes; --"
    with pytest.raises(ValidationError):
        Filter.model_validate(location_config)


def test_etl_validates_real_columns_for_simple_and_location_filters(location_config):
    from etl.dataset import DatasetProcessor, FilterError
    from etl.models import Column, Filter

    processor = DatasetProcessor.__new__(DatasetProcessor)
    location = Filter.model_validate(location_config)
    columns = [Column(name=field.column, hidden=True) for field in location.extras.fields]
    simple = Filter(id="region", title="Region", target_column=columns[0].name, type="match")
    # A virtual location target is valid; all referenced raw columns must exist.
    processor.validate_query_columns(columns, [simple, location])
    with pytest.raises(FilterError, match="unknown columns"):
        processor.validate_query_columns([], [simple])
    with pytest.raises(FilterError, match="unknown columns"):
        processor.validate_query_columns([], [location])

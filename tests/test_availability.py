import pandas as pd


def is_available(availability_lookup, ta, slot):
    try:
        value = availability_lookup.loc[ta, slot]
        return str(value).strip() in ["\u2713", "True", "TRUE", "true"]
    except KeyError:
        return False
    except Exception:
        return False


def mock_lookup():
    df = pd.DataFrame({
        "TA Name": ["Alice", "Bob"],
        "Monday P1": ["\u2713", True],
        "Monday P2": ["", None],
    })
    return df.set_index("TA Name").replace("\u2713", True).fillna(False)


def test_true_values():
    lookup = mock_lookup()
    assert is_available(lookup, "Alice", "Monday P1") is True
    assert is_available(lookup, "Bob", "Monday P1") is True


def test_blank_or_missing_values():
    lookup = mock_lookup()
    assert is_available(lookup, "Alice", "Monday P2") is False
    assert is_available(lookup, "Bob", "Nonexistent") is False

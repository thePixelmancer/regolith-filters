from recipe_image_gen import flatten_pattern


def test_flatten_pattern_basic():
    pattern = ["AB", "C"]
    key = {"A": {"item": "item_a"}, "B": {"item": "item_b"}, "C": {"item": "item_c"}}

    result = flatten_pattern(pattern, key)
    assert result == ["item_a", "item_b", None, "item_c", None, None, None, None, None]


def test_flatten_pattern_empty():
    pattern = []
    key = {}

    result = flatten_pattern(pattern, key)
    assert result == [None] * 9  # Expecting a flat list of 9 None values


def test_flatten_pattern_full():
    pattern = ["ABC", "DEF", "GHI"]
    key = {
        "A": {"item": "item_a"},
        "B": {"item": "item_b"},
        "C": {"item": "item_c"},
        "D": {"item": "item_d"},
        "E": {"item": "item_e"},
        "F": {"item": "item_f"},
        "G": {"item": "item_g"},
        "H": {"item": "item_h"},
        "I": {"item": "item_i"},
    }

    result = flatten_pattern(pattern, key)
    assert result == [
        "item_a",
        "item_b",
        "item_c",
        "item_d",
        "item_e",
        "item_f",
        "item_g",
        "item_h",
        "item_i",
    ]


test_flatten_pattern_basic()
test_flatten_pattern_empty()
test_flatten_pattern_full()

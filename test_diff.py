from diff import read_block


def splitlines(text: str) -> list[str]:
    return [str(t)[4:] for t in text.splitlines()]


def test_basic_block():
    text = """
    1one
    2two
    3three
    """
    _, block = read_block(splitlines(text))
    assert block == {"1one": {}, "2two": {}, "3three": {}}


def test_equality():
    text1 = """
    1one
    2two
    3three
    """
    text2 = """
    2two
    1one
    3three
    """
    _, block1 = read_block(splitlines(text1))
    _, block2 = read_block(splitlines(text2))
    assert block1 == block2


def test_block_ignores():
    text = """
    1one
    !
    2two

    3three
    !!!!ignore
    """
    _, block = read_block(splitlines(text))
    assert block == {"1one": {}, "2two": {}, "3three": {}}


def test_simple_sub_block():
    text = """
    1one
    2two
    3three
        bbb
        ccc
        aaa
    4four
    5five
    """
    _, block = read_block(splitlines(text))
    assert block == {
        "1one": {},
        "2two": {},
        "3three": {"bbb": {}, "ccc": {}, "aaa": {}},
        "4four": {},
        "5five": {},
    }


def test_nested_block():
    text = """
    1one
    2two
    3three
        bbb
        ccc
        aaa
            111one
            222two
            333three
                bbb
                ccc
                aaa
            444four
            555five
    """
    _, block = read_block(splitlines(text))
    assert block == {
        "1one": {},
        "2two": {},
        "3three": {
            "bbb": {},
            "ccc": {},
            "aaa": {
                "111one": {},
                "222two": {},
                "333three": {
                    "bbb": {},
                    "ccc": {},
                    "aaa": {},
                },
                "444four": {},
                "555five": {},
            },
        },
    }


def test_multiple_blocks():
    text = """
    1one
    2two
        bbb
        ccc
        aaa
    3three
        bbb
        ccc
        aaa
    4four
    """
    _, block = read_block(splitlines(text))
    assert block == {
        "1one": {},
        "2two": {"bbb": {}, "ccc": {}, "aaa": {}},
        "3three": {"bbb": {}, "ccc": {}, "aaa": {}},
        "4four": {},
    }

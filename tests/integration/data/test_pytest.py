import clean_air.data.inc_dec as idec   # The code to test

def test_increment():
    assert idec.increment(3) == 4

def test_decrement():
    assert idec.decrement(3) == 4
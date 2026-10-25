"""The 5-wire code must match the printed sheets (wires.js in bible-ai-preado)."""

from alfabet_pe_fire.encoding import SYMBOLS, Symbol, encode, encode_char


def test_31_symbols_codes_1_to_31():
    assert len(SYMBOLS) == 31
    assert encode_char("A") == Symbol("A", 1)
    assert encode_char("Ț").code == 28
    assert [encode_char(c).code for c in "PRUV"] == [16, 17, 20, 21]  # no Q
    assert [encode_char(c).code for c in " ,."] == [29, 30, 31]


def test_lowercase_and_diacritics():
    assert encode("ăâîșț") == encode("ĂÂÎȘȚ")
    # cedilla forms (old keyboards) become comma forms
    assert encode("şţ") == encode("șț")


def test_q_w_y_and_quotes_are_skipped():
    assert encode("QWY„”'\"") == []
    assert encode("ß") == []  # upper-cases to two letters


def test_fallbacks():
    assert [s.char for s in encode("!?:;-")] == [".", ".", ",", ",", " "]


def test_bits_wire_1_is_most_significant():
    s = Symbol("V", 21)
    assert s.binary == "10101"
    assert s.bits == (True, False, True, False, True)
    assert Symbol(".", 31).bits == (True,) * 5
    assert Symbol(" ", 29).label == "␣"
    assert encode_char("L").detail == "01100 · 12"


def test_same_codes_as_wires_js():
    # produced by encode(ch, 5) from bible-ai-preado src/shared/wires.js
    msg = "Felul vostru de vorbire să fie: „Da, da; nu, nu”; şi ţie! Wow? a-b Quiz."
    assert [s.code for s in encode(msg)] == [6,5,12,20,12,29,21,15,18,19,17,20,29,4,5,29,21,15,17,2,9,17,5,29,18,24,29,6,9,5,30,29,4,1,30,29,4,1,30,29,14,20,30,29,14,20,30,29,27,9,29,28,9,5,31,29,15,31,29,1,29,2,29,20,9,23,31]

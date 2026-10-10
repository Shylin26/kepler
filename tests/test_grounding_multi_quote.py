"""
Tests for multi-quote grounding. check_grounding_multi() must:
- accept several quotes that are EACH contiguous substrings of the output
- still reject a spliced quote (joined across non-contiguous lines)
- reject if ANY quote is ungrounded
- reject an empty list
"""
from agents.analyst.analyst_agent import check_grounding_multi

OUTPUT = (
    "Training with small batch size (32):\n"
    "Batch size 32, Epoch 1, Avg Loss: 91.7677\n"
    "Batch size 32, Epoch 5, Avg Loss: 52.1695\n\n"
    "Training with large batch size (1024):\n"
    "Batch size 1024, Epoch 1, Avg Loss: 5.2305\n"
    "Batch size 1024, Epoch 5, Avg Loss: 5.1099\n"
)

def test_two_separate_contiguous_quotes_pass():
    quotes = ["Batch size 32, Epoch 5, Avg Loss: 52.1695",
              "Batch size 1024, Epoch 5, Avg Loss: 5.1099"]
    assert check_grounding_multi(quotes, OUTPUT)["grounded"] is True

def test_spliced_quote_still_rejected():
    spliced = ["Batch size 32, Epoch 5, Avg Loss: 52.1695\nBatch size 1024, Epoch 5, Avg Loss: 5.1099"]
    r = check_grounding_multi(spliced, OUTPUT)
    assert r["grounded"] is False

def test_one_bad_quote_fails_all():
    quotes = ["Batch size 32, Epoch 5, Avg Loss: 52.1695", "inconclusive"]
    assert check_grounding_multi(quotes, OUTPUT)["grounded"] is False

def test_empty_list_rejected():
    assert check_grounding_multi([], OUTPUT)["grounded"] is False

def test_wrapping_quotes_stripped_but_splice_still_rejected():
    wrapped = ['"Batch size 32, Epoch 5, Avg Loss: 52.1695"']
    assert check_grounding_multi(wrapped, OUTPUT)["grounded"] is True
    spliced = ['"Batch size 32, Epoch 5, Avg Loss: 52.1695\nBatch size 1024, Epoch 5, Avg Loss: 5.1099"']
    assert check_grounding_multi(spliced, OUTPUT)["grounded"] is False
if __name__ == "__main__":
    test_two_separate_contiguous_quotes_pass()
    test_spliced_quote_still_rejected()
    test_one_bad_quote_fails_all()
    test_empty_list_rejected()
    test_wrapping_quotes_stripped_but_splice_still_rejected()
    print("All multi-quote grounding tests passed.")
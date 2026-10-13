"""
check_numeric_direction() must ignore numbers that are labels (batch size,
LR=, seed, epoch) and compare result values. It must still catch a real
backwards comparison.
"""
from agents.analyst.analyst_agent import check_numeric_direction

def test_batch_size_labels_ignored():
    # Correct reasoning. 1024 and 32 are labels; losses are 5.1 vs 52.2.
    r = check_numeric_direction(
        "The loss for batch size 1024 (5.1) is lower than for batch size 32 (52.2).")
    assert r["checked"] is False or r["consistent"] is True

def test_lr_label_ignored():
    r = check_numeric_direction(
        "With LR=0.01 the accuracy of 0.57 is lower than 1.00.")
    assert r["checked"] is False or r["consistent"] is True

def test_real_backwards_comparison_still_caught():
    # 0.89 vs 0.91 described as higher -> wrong, must be flagged.
    r = check_numeric_direction("The score of 0.89 is higher than 0.91.")
    assert r["checked"] is True and r["consistent"] is False

def test_correct_comparison_passes():
    r = check_numeric_direction("The score of 0.91 is higher than 0.89.")
    assert r["checked"] is True and r["consistent"] is True

if __name__ == "__main__":
    test_batch_size_labels_ignored()
    test_lr_label_ignored()
    test_real_backwards_comparison_still_caught()
    test_correct_comparison_passes()
    print("All numeric-direction label tests passed.")
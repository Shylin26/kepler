from agents.analyst.analyst_agent import analyze_result, _normalize_for_grounding

output = (
    "Training with small batch size (32):\n"
    "Batch size 32, Epoch 1, Avg Loss: 91.7677\n"
    "Batch size 32, Epoch 2, Avg Loss: 78.2924\n"
    "Batch size 32, Epoch 3, Avg Loss: 69.1715\n"
    "Batch size 32, Epoch 4, Avg Loss: 58.6740\n"
    "Batch size 32, Epoch 5, Avg Loss: 52.1695\n\n"
    "Training with large batch size (1024):\n"
    "Batch size 1024, Epoch 1, Avg Loss: 5.2305\n"
    "Batch size 1024, Epoch 2, Avg Loss: 5.2001\n"
    "Batch size 1024, Epoch 3, Avg Loss: 5.1698\n"
    "Batch size 1024, Epoch 4, Avg Loss: 5.1398\n"
    "Batch size 1024, Epoch 5, Avg Loss: 5.1099\n"
)

for i in range(5):
    r = analyze_result(
        "A larger batch size reduces the variance of gradient estimates, leading to smoother loss curves compared to a smaller batch size.",
        "The loss curves for the larger batch size should be smoother compared to those with the smaller batch size.",
        output,
    )
    print(f"--- run {i+1}: verdict={r['verdict']} ---")
    print("REASONING:", r.get("reasoning"))
    if "rejected_quotes" in r:
        print("REJECTED QUOTES:", repr(r["rejected_quotes"]))
    else:
        print("quotes accepted:", repr(r.get("supporting_quotes")))
def cap_output(output: str, max_chars: int = 12000) -> str:
    """Keep the head and tail of long output, with an explicit marker, so the
    prompt can't overflow the context window and push the task out."""
    if len(output) <= max_chars:
        return output
    half = max_chars // 2
    omitted = len(output) - 2 * half
    return output[:half] + f"\n[... {omitted} characters omitted ...]\n" + output[-half:]
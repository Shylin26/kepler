def basic_sanity_check(sandbox_result:dict)->dict:
    exit_code=sandbox_result.get("exit_code")
    output=sandbox_result.get("output","")
    if exit_code!=0:
        return {"passed":False,"reason":f"Non-zero exit code: {exit_code}. Output: {output.strip()[:200]}"}
    if not output.strip():
        return {"passed": False, "reason": "Script ran successfully but produced no output at all."}
    
    error_keywords=["Traceback","Error","Exception"]
    if any(keyword in output for keyword in error_keywords):
        return {"passed": False, "reason": f"Output contains error-like text despite exit code 0: {output.strip()[:200]}"}

    return {"passed": True, "reason": "Passed basic sanity checks."}


if __name__ == "__main__":
    
    good_result = {"exit_code": 0, "output": "[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]\n"}
    print("--- CASE 1: good result ---")
    print(basic_sanity_check(good_result))

    
    silent_result = {"exit_code": 0, "output": ""}
    print("--- CASE 2: silent success ---")
    print(basic_sanity_check(silent_result))

    
    crash_result = {"exit_code": 1, "output": "Traceback (most recent call last):\nZeroDivisionError: division by zero"}
    print("--- CASE 3: crash ---")
    print(basic_sanity_check(crash_result))
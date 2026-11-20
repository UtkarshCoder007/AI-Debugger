from harness.grader import grade, load_key
from harness.loop import run_agent

if __name__ == "__main__":
    result = run_agent("shop_v1")
    print(f"\nstatus: {result['status']} | steps: {result['steps']} | tokens: {result['tokens']}")
    print(f"files read: {', '.join(result['files_read']) or 'none'} | tests run: {result['tests_run']}x")
    print("\nSubmitted findings:")
    for f in result["findings"]:
        print(f"  {f['file']}:{f['line']}  {f['description']}")
    g = grade(result["findings"], load_key("shop_v1"))
    print(f"\nfound {len(g['found'])}/5: {', '.join(g['found']) or '-'}")
    print(f"missed: {', '.join(g['missed']) or '-'} | false positives: {g['false_positives']}")
    print(f"log: runs/{result['run_id']}/log.jsonl")
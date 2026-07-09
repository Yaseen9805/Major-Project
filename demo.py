"""Live demo: type a question, see baseline vs adaptive side by side.

Run: python demo.py
Try asking the same question twice, or a paraphrase of it, right after --
the second call to the adaptive system should show cache_hit=True and an
almost-instant response.
"""

from adaptive import ask_adaptive
from baseline import ask_baseline

running_baseline_cost = 0.0
running_adaptive_cost = 0.0


def print_result(label: str, result: dict) -> None:
    cache_note = ""
    if label == "ADAPTIVE":
        cache_note = f", cache_hit={result['cache_hit']}, tier={result['tier_used']}"
    print(
        f"[{label}] ({result['latency_ms']:.0f}ms, cost={result['estimated_cost']:.6f}{cache_note})\n"
        f"  {result['answer']}\n"
    )


def main() -> None:
    global running_baseline_cost, running_adaptive_cost

    print("CostQual-Router live demo. Type a question, or 'quit' to exit.")
    print("Tip: ask the same question twice (or a paraphrase) to see a cache hit.\n")

    while True:
        query = input("> ").strip().lstrip(chr(0xFEFF))
        if not query:
            continue
        if query.lower() in ("quit", "exit"):
            break

        baseline_result = ask_baseline(query)
        adaptive_result = ask_adaptive(query)

        running_baseline_cost += baseline_result["estimated_cost"]
        running_adaptive_cost += adaptive_result["estimated_cost"]

        print_result("BASELINE", baseline_result)
        print_result("ADAPTIVE", adaptive_result)
        savings_pct = (
            (running_baseline_cost - running_adaptive_cost) / running_baseline_cost * 100
            if running_baseline_cost
            else 0
        )
        print(
            f"Running total -- baseline cost: {running_baseline_cost:.6f}, "
            f"adaptive cost: {running_adaptive_cost:.6f} ({savings_pct:.0f}% saved so far)\n"
        )


if __name__ == "__main__":
    main()

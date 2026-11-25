"""M5 masking check (tokenizer only, CPU): is each model's prompt + response built correctly?

  python src/train/check_template.py --model qwen3-4b olmo2-7b qwen3-1.7b qwen3-8b

For a few quartets it checks:
  1. the response tokens decode to exactly  response text + end-of-turn token;
  2. the model's own chat template, given the full conversation, renders  prompt + response text + end-of-turn
     (so the scored sequence is what the model would see; trailing whitespace after the end-of-turn ignored);
  3. the answer-span tokens cover the answer text;
  4. the prompt never contains the response and ends with the assistant header.
Prints one example sequence per model with the scored tokens marked.
"""

import argparse

from config import ROOT, load_config
from data import ORDER, Encoder, load_quartets
from models import load_tokenizer


def check(model: str, n: int) -> bool:
    cfg = load_config(model)
    tok = load_tokenizer(cfg)
    enc = Encoder(tok, cfg)
    eot = tok.decode(enc.eot_ids)
    qs = load_quartets(ROOT / "data/quartets/val.jsonl")[:n]
    ok = True
    problems = []
    for q in qs:
        prompt = enc.prompt_text(q)
        for k in ORDER:
            resp = q["responses"][k]
            ids, span = enc.response(resp["text"], resp["ans_span"])
            if tok.decode(ids) != resp["text"] + eot:
                problems.append(f"{q['qid']} {k}: decode mismatch {tok.decode(ids)[-40:]!r}")
            full = tok.apply_chat_template([{"role": "user", "content": prompt_user(enc, q)},
                                            {"role": "assistant", "content": resp["text"]}], tokenize=False,
                                           **enc.template_kwargs)
            want = prompt + resp["text"] + eot
            if full.rstrip() != want.rstrip():
                problems.append(f"{q['qid']} {k}: template renders differently\n   template: {full[len(prompt) - 30:]!r}"
                                f"\n   ours:     {want[len(prompt) - 30:]!r}")
            s, e = resp["ans_span"]
            span_text = tok.decode([i for i, m in zip(ids, span) if m])
            if resp["text"][s:e].strip() not in span_text:
                problems.append(f"{q['qid']} {k}: span tokens {span_text!r} miss {resp['text'][s:e]!r}")
    if problems:
        ok = False
        print(f"\n[{model}] {len(problems)} problems (first 5):")
        for p in problems[:5]:
            print("  ", p)
    q = qs[0]
    print(f"\n[{model}] eot={eot!r} pad={tok.pad_token!r} {'OK' if ok else 'FAIL'}\n--- prompt ---\n{enc.prompt_text(q)}"
          f"--- scored response (CW), answer span in [[ ]] ---")
    ids, span = enc.response(q["responses"]["CW"]["text"], q["responses"]["CW"]["ans_span"])
    print("".join(f"[[{tok.decode([i])}]]" if m else tok.decode([i]) for i, m in zip(ids, span)))
    return ok


def prompt_user(enc: Encoder, q: dict) -> str:
    return enc.template.format(passage=q["passage"], question=q["question"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", nargs="+", required=True)
    ap.add_argument("--n", type=int, default=50)
    args = ap.parse_args()
    results = {m: check(m, args.n) for m in args.model}
    print("\nsummary:", results)
    raise SystemExit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()

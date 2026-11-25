"""M5 open-book vs closed-book check: how often does the UNTRAINED model answer correctly?

  python src/train/openbook.py --model qwen3-4b            # 200 val + 200 SciQ questions, both prompts

Greedy generation (thinking off), max 64 new tokens. A generation is correct if it contains the correct
answer and not the wrong answer (normalised, whole words; yes/no questions: the right word and not the other).
  open-book    = the training prompt (plan §5.10)
  closed-book  = "Answer the question.\n\nQuestion: {question}"
Decision rule (plan §5.10, §18): keep open-book if its accuracy is clearly below ceiling (~90–95%).
Writes runs/<model>/m5/openbook.json (accuracies) and openbook_generations.jsonl.
"""

import argparse
import json
import re

import numpy as np
import torch

from config import ROOT, load_config
from data import load_quartets
from models import load_model, load_tokenizer

CLOSED = "Answer the question.\n\nQuestion: {question}"


def norm(s: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", s.lower()).split())


def contains(text: str, phrase: str) -> bool:
    p = norm(phrase)
    return bool(p) and re.search(rf"(?<!\w){re.escape(p)}(?!\w)", norm(text)) is not None


def score(gen: str, correct: str, wrong: str) -> dict:
    if norm(correct) in ("yes", "no"):
        other = "no" if norm(correct) == "yes" else "yes"
        c, w = contains(gen, correct), contains(gen, other)
    else:
        c = contains(gen, correct)
        w = contains(gen, wrong) and norm(wrong) not in norm(correct)
    return {"has_correct": c, "has_wrong": w, "correct": c and not w}


@torch.no_grad()
def generate(model, tok, prompts: list[str], bs: int, max_new: int) -> list[str]:
    tok.padding_side = "left"
    out = []
    for i in range(0, len(prompts), bs):
        b = tok(prompts[i:i + bs], return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
        g = model.generate(**b, max_new_tokens=max_new, do_sample=False, pad_token_id=tok.pad_token_id)
        out += tok.batch_decode(g[:, b["input_ids"].shape[1]:], skip_special_tokens=True)
        print(f"  {min(i + bs, len(prompts))}/{len(prompts)}", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--splits", nargs="+", default=["val", "ood_sciq"])
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--max-new", type=int, default=64)
    ap.add_argument("--set", nargs="*", default=[], help="config overrides key=value")
    args = ap.parse_args()
    cfg = load_config(args.model, args.set)
    tok = load_tokenizer(cfg)
    model = load_model(cfg, tok)
    kw = cfg["model"].get("chat_template_kwargs") or {}

    def chat(user):
        return tok.apply_chat_template([{"role": "user", "content": user}], tokenize=False,
                                       add_generation_prompt=True, **kw)

    out_dir = ROOT / cfg["output"]["reference_root"] / cfg["model"]["name"] / "m5"
    out_dir.mkdir(parents=True, exist_ok=True)
    report, rows = {}, []
    for split in args.splits:
        qs = load_quartets(ROOT / "data/quartets" / f"{split}.jsonl")
        pick = np.random.default_rng(0).choice(len(qs), size=min(args.n, len(qs)), replace=False)
        qs = [qs[i] for i in sorted(pick)]
        for mode in ("open", "closed"):
            users = [(cfg["prompt"]["template"] if mode == "open" else CLOSED).format(passage=q["passage"],
                                                                                      question=q["question"]) for q in qs]
            print(f"{split} {mode}-book: {len(qs)} questions")
            gens = generate(model, tok, [chat(u) for u in users], args.batch, args.max_new)
            scores = [score(g, q["correct_answer"], q["wrong_answer"]) for g, q in zip(gens, qs)]
            report[f"{split}/{mode}"] = {k: round(float(np.mean([s[k] for s in scores])), 4)
                                         for k in ("correct", "has_correct", "has_wrong")}
            rows += [{"split": split, "mode": mode, "qid": q["qid"], "question": q["question"],
                      "correct_answer": q["correct_answer"], "wrong_answer": q["wrong_answer"], "generation": g, **s}
                     for g, q, s in zip(gens, qs, scores)]
            print(f"  -> {report[f'{split}/{mode}']}")
    json.dump(report, open(out_dir / "openbook.json", "w"), indent=1)
    with open(out_dir / "openbook_generations.jsonl", "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()

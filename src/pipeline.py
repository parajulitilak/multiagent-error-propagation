"""Multi-agent pipeline under study: Decomposer -> Solver -> Verifier.

Every run returns a full trace (all intermediate messages plus per-stage
token usage) so that analysis is decoupled from expensive API calls. Traces
are the dataset of this study.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Optional

# --- LLM call wrapper (provider-agnostic) -----------------------------------

def call_llm(system: str, user: str, cfg: dict) -> tuple[str, dict]:
    """Single LLM call with retries. Returns (text, token_usage).
    Provider chosen in configs/experiment.yaml."""
    provider = cfg.get("provider", "anthropic")
    last_err: Exception | None = None
    for attempt in range(4):
        try:
            if provider == "anthropic":
                import anthropic
                client = anthropic.Anthropic()  # key from ANTHROPIC_API_KEY in .env
                resp = client.messages.create(
                    model=cfg["model"],
                    max_tokens=cfg.get("max_tokens", 1024),
                    temperature=cfg.get("temperature", 0.0),
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                usage = {"input_tokens": resp.usage.input_tokens,
                         "output_tokens": resp.usage.output_tokens}
                return resp.content[0].text, usage
            else:  # openai
                from openai import OpenAI
                client = OpenAI()  # key from OPENAI_API_KEY
                resp = client.chat.completions.create(
                    model=cfg["model"],
                    max_tokens=cfg.get("max_tokens", 1024),
                    temperature=cfg.get("temperature", 0.0),
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                usage = {"input_tokens": resp.usage.prompt_tokens,
                         "output_tokens": resp.usage.completion_tokens}
                return resp.choices[0].message.content, usage
        except Exception as e:  # rate limits, transient network errors
            last_err = e
            time.sleep(2**attempt)
    raise RuntimeError(f"LLM call failed after retries: {last_err}")


# --- Agent role prompts ------------------------------------------------------

DECOMPOSER_SYS = (
    "You are a planning agent. Break the problem into a short numbered plan of "
    "2-5 concrete steps with any intermediate quantities needed. Do NOT solve it. "
    "Output only the plan."
)
SOLVER_SYS = (
    "You are a solving agent. Execute the given plan step by step on the problem. "
    "Show brief working, then end with the line: FINAL ANSWER: <answer>."
)
VERIFIER_SYS = (
    "You are a verification agent. Check the proposed solution against the "
    "original problem. If correct, reply 'VERDICT: ACCEPT'. If you find an error, "
    "reply 'VERDICT: REJECT', explain the error in one sentence, and give a "
    "corrected line: FINAL ANSWER: <answer>."
)
SINGLE_SYS = (
    "Solve the problem step by step. End with the line: FINAL ANSWER: <answer>."
)


@dataclass
class Trace:
    """Full record of one problem run. Serialised to JSONL by the runner."""
    problem_id: str
    condition: str
    question: str
    gold: str
    plan: Optional[str] = None
    plan_after_injection: Optional[str] = None
    injection_meta: Optional[dict] = None
    solution: Optional[str] = None
    solution_after_injection: Optional[str] = None
    verifier_output: Optional[str] = None
    verifier_verdict: Optional[str] = None  # ACCEPT | REJECT | None
    final_answer: Optional[str] = None
    usage: dict = field(default_factory=dict)  # per-stage token counts
    extra: dict = field(default_factory=dict)


def run_single_agent(question: str, cfg: dict) -> tuple[str, dict]:
    return call_llm(SINGLE_SYS, question, cfg)


def run_pipeline(
    question: str,
    cfg: dict,
    inject_stage: Optional[str] = None,   # None | 'decomposer' | 'solver'
    injector=None,                        # fn(text, rng) -> (corrupted, meta)
    rng=None,
    use_verifier: bool = True,
) -> Trace:
    t = Trace(problem_id="", condition="", question=question, gold="")

    # Stage 1: Decomposer
    t.plan, t.usage["decomposer"] = call_llm(DECOMPOSER_SYS, question, cfg)
    plan_used = t.plan
    if inject_stage == "decomposer" and injector is not None:
        plan_used, t.injection_meta = injector(t.plan, rng)
        t.plan_after_injection = plan_used

    # Stage 2: Solver
    solver_input = f"PROBLEM:\n{question}\n\nPLAN:\n{plan_used}"
    t.solution, t.usage["solver"] = call_llm(SOLVER_SYS, solver_input, cfg)
    solution_used = t.solution
    if inject_stage == "solver" and injector is not None:
        solution_used, t.injection_meta = injector(t.solution, rng)
        t.solution_after_injection = solution_used

    # Stage 3: Verifier (ablatable)
    if use_verifier:
        v_input = f"PROBLEM:\n{question}\n\nPROPOSED SOLUTION:\n{solution_used}"
        t.verifier_output, t.usage["verifier"] = call_llm(VERIFIER_SYS, v_input, cfg)
        t.verifier_verdict = (
            "REJECT" if "VERDICT: REJECT" in t.verifier_output.upper() else
            "ACCEPT" if "VERDICT: ACCEPT" in t.verifier_output.upper() else None
        )

    # Final answer: the verifier's correction wins on REJECT, but only if it
    # actually gave one; falling back to the last number in the rejection
    # prose would score an arbitrary quantity.
    if t.verifier_verdict == "REJECT":
        corrected = extract_marked_answer(t.verifier_output)
        if corrected is None:
            t.extra["verifier_gave_no_answer"] = True
            t.final_answer = extract_final_answer(solution_used)
        else:
            t.final_answer = corrected
    else:
        t.final_answer = extract_final_answer(solution_used)
    return t


def extract_marked_answer(text: Optional[str]) -> Optional[str]:
    """Answer after the last 'FINAL ANSWER:' marker, or None if no marker.

    Only the marker's own line is taken, and a later marker on the same line
    wins (verifiers sometimes quote the rejected answer before correcting it).
    """
    if not text:
        return None
    parts = re.split(r"FINAL ANSWER:\s*", text, flags=re.IGNORECASE)
    if len(parts) < 2:
        return None
    tail = parts[-1].split("\n", 1)[0].strip()
    return tail or None


def extract_final_answer(text: Optional[str]) -> str:
    """Marked answer if present, else the last number in the text."""
    marked = extract_marked_answer(text)
    if marked is not None:
        return marked
    if text is None:
        return ""
    nums = re.findall(r"-?\d[\d,]*\.?\d*", text)
    return nums[-1].replace(",", "") if nums else ""

"""Simulation engine for ICR Lab.

Generates synthetic interaction traces for different prompting modes,
showing how interaction architecture affects token consumption.
"""

import hashlib
import math
from dataclasses import dataclass, field


@dataclass
class InteractionRound:
    """A single round of interaction between user and AI system."""

    round_number: int
    input_tokens: int
    output_tokens: int
    cumulative_tokens: int
    description: str
    prompt_text: str = ""
    token_source: str = "estimated"
    assumptions: list[str] = field(default_factory=list)


@dataclass
class SimulationResult:
    """Complete simulation result for one mode."""

    mode: str
    rounds: list[InteractionRound]
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    operations_achieved: int
    optimized_prompt: str = ""
    total_assumptions: int = 0
    wrong_assumptions: int = 0


def _task_complexity(task: str) -> int:
    """Derive a deterministic complexity score from the task string."""
    hash_val = int(hashlib.md5(task.encode()).hexdigest()[:8], 16)
    word_count = len(task.split())
    return 5 + (hash_val % 6) + min(word_count // 3, 5)


def _base_tokens(task: str) -> int:
    """Base token count derived from task complexity."""
    return _task_complexity(task) * 120


def _build_result(
    mode: str, base: int, operations: int, round_specs: list[tuple[float, float, str]]
) -> SimulationResult:
    """Build a SimulationResult from a list of (input_mult, output_mult, description) tuples."""
    rounds = []
    cumulative = 0
    for i, (in_mult, out_mult, desc) in enumerate(round_specs, 1):
        inp = int(base * in_mult)
        out = int(base * out_mult)
        cumulative += inp + out
        rounds.append(
            InteractionRound(
                round_number=i,
                input_tokens=inp,
                output_tokens=out,
                cumulative_tokens=cumulative,
                description=desc,
            )
        )
    total_input = sum(r.input_tokens for r in rounds)
    total_output = sum(r.output_tokens for r in rounds)
    return SimulationResult(
        mode=mode,
        rounds=rounds,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=total_input + total_output,
        operations_achieved=operations,
    )


# --- Mode configs: (input_multiplier, output_multiplier, description) per round ---

_VERBOSE_ROUNDS = [
    (8.0, 4.0, "Full context dump with repeated explanations and examples"),
    (6.0, 3.0, "Re-explained requirements with additional verbose context"),
]

_CONTEXT_AWARE_ROUNDS = [
    (3, 2, "Structured request with relevant context"),
    (1.5, 1.5, "Refinement using context references (not repetition)"),
    (1, 1.2, "Final execution with compressed context"),
]

_INTENT_OPTIMIZED_ROUNDS = [
    (1.2, 1.8, "Single compressed intent \u2014 system resolves dependency graph"),
]

_CLARIFICATION_DESCRIPTIONS = [
    "Initial vague request",
    "Clarification: what exactly do you mean?",
    "Follow-up: which components specifically?",
    "More detail: what about dependencies?",
    "Confirmation: let me restate everything",
    "Adjustment: actually, also include...",
    "Final confirmation with full restated context",
    "Execution with accumulated context",
]


def _clarification_rounds(task: str) -> list[tuple[float, float, str]]:
    """Generate dynamic round specs for clarification mode (context grows each round)."""
    num_rounds = 5 + (_task_complexity(task) % 4)
    return [
        (
            1.5 * (1.0 + i * 0.4),
            0.8,
            _CLARIFICATION_DESCRIPTIONS[min(i, len(_CLARIFICATION_DESCRIPTIONS) - 1)],
        )
        for i in range(num_rounds)
    ]


_ASSUMPTION_DESCRIPTIONS = [
    "Agent infers missing context and executes with stated assumptions",
    "Correction round: user identifies a wrong assumption",
    "Re-execution with corrected parameters",
    "Second correction: additional assumption was wrong",
    "Final re-execution with all corrections applied",
]


def _assumption_led_rounds(wrong: int) -> list[tuple[float, float, str]]:
    """Generate round specs for assumption-led mode given the number of wrong assumptions.

    Round 1: agent states assumptions and executes (low input — user said little,
    higher output — agent infers and acts). Subsequent rounds are corrections
    for wrong assumptions.
    """
    rounds = [
        (
            0.6,
            1.4,
            _ASSUMPTION_DESCRIPTIONS[0],
        )
    ]
    for i in range(wrong):
        rounds.append(
            (
                1.8 + i * 0.4,
                0.9,
                _ASSUMPTION_DESCRIPTIONS[min(i + 1, len(_ASSUMPTION_DESCRIPTIONS) - 1)],
            )
        )
    if wrong > 0:
        rounds.append(
            (
                1.2,
                1.6,
                _ASSUMPTION_DESCRIPTIONS[
                    min(wrong + 1, len(_ASSUMPTION_DESCRIPTIONS) - 1)
                ],
            )
        )
    return rounds


def _simulate_assumption_led(
    task: str, operations: int, accuracy: float = 1.0
) -> "SimulationResult":
    """Simulate Assumption Led mode with caller-controlled accuracy.

    Args:
        task: The task description.
        operations: Number of operations the task requires.
        accuracy: Fraction of assumptions that are correct (0.0–1.0).
                  1.0 = perfect (0 wrong), 0.0 = all wrong.

    ops_achieved scales directly with accuracy so that every task shows
    visible coverage changes across the full slider range, regardless of
    total_a (number of assumptions derived from task complexity).
    wrong count still drives correction-round structure for token inflation.
    """
    c = _task_complexity(task)
    total_a = 1 + (c % 3)
    wrong = min(math.ceil(total_a * (1 - accuracy)), total_a)
    # Direct proportional model: accuracy fraction of ops actually complete
    ops_achieved = math.floor(operations * accuracy)
    result = _build_result(
        "Assumption Led",
        _base_tokens(task),
        ops_achieved,
        _assumption_led_rounds(wrong),
    )
    result.total_assumptions = total_a
    result.wrong_assumptions = wrong
    return result


_OVER_COMPRESSED_ROUNDS = [
    (0.8, 0.6, "Over-compressed intent — system misinterprets scope"),
    (2.5, 1.5, "Correction: user explains what was missed"),
    (3.0, 2.0, "Re-correction: implicit constraints not captured"),
    (4.0, 2.5, "Full restatement with explicit ordering and dependencies"),
    (2.0, 2.0, "Final execution after accumulated corrections"),
]

# Natural completion fraction per mode — how many ops each mode achieves without override.
# Clarification Heavy stalls before execution; Over Compressed misses ~half.
_MODE_COMPLETION: dict[str, float] = {
    "Verbose Prompting": 1.0,
    "Clarification Heavy": 0.0,
    "Context Aware": 1.0,
    "Intent Optimized": 1.0,
    "Over Compressed": 0.5,
    "Assumption Led": 1.0,
}


def _simulate(
    mode: str, task: str, operations: int, round_specs: list[tuple[float, float, str]]
) -> SimulationResult:
    ops_achieved = int(operations * _MODE_COMPLETION.get(mode, 1.0))
    return _build_result(mode, _base_tokens(task), ops_achieved, round_specs)


# Mode registry
SIMULATION_MODES = {
    "Verbose Prompting": lambda t, ops: _simulate(
        "Verbose Prompting", t, ops, _VERBOSE_ROUNDS
    ),
    "Clarification Heavy": lambda t, ops: _simulate(
        "Clarification Heavy", t, ops, _clarification_rounds(t)
    ),
    "Context Aware": lambda t, ops: _simulate(
        "Context Aware", t, ops, _CONTEXT_AWARE_ROUNDS
    ),
    "Intent Optimized": lambda t, ops: _simulate(
        "Intent Optimized", t, ops, _INTENT_OPTIMIZED_ROUNDS
    ),
    "Over Compressed": lambda t, ops: _simulate(
        "Over Compressed", t, ops, _OVER_COMPRESSED_ROUNDS
    ),
    "Assumption Led": lambda t, ops: _simulate_assumption_led(t, ops),
}


def apply_output_compression(
    results: list[SimulationResult], factor: float
) -> list[SimulationResult]:
    """Apply output compression to all results (simulates Caveman-style terse responses).

    Args:
        results: List of SimulationResult from run_simulation.
        factor: Multiplier for output tokens (0.65 = 35% reduction).

    Returns:
        New list of SimulationResult with compressed output tokens.
    """
    if factor >= 1.0:
        return results

    compressed = []
    for r in results:
        new_rounds = []
        cumulative = 0
        for rd in r.rounds:
            new_out = int(rd.output_tokens * factor)
            cumulative += rd.input_tokens + new_out
            new_rounds.append(
                InteractionRound(
                    round_number=rd.round_number,
                    input_tokens=rd.input_tokens,
                    output_tokens=new_out,
                    cumulative_tokens=cumulative,
                    description=rd.description,
                    prompt_text=rd.prompt_text,
                    token_source=rd.token_source,
                    assumptions=rd.assumptions,
                )
            )
        total_input = sum(rd.input_tokens for rd in new_rounds)
        total_output = sum(rd.output_tokens for rd in new_rounds)
        compressed.append(
            SimulationResult(
                mode=r.mode,
                rounds=new_rounds,
                total_input_tokens=total_input,
                total_output_tokens=total_output,
                total_tokens=total_input + total_output,
                operations_achieved=r.operations_achieved,
                optimized_prompt=r.optimized_prompt,
                total_assumptions=r.total_assumptions,
                wrong_assumptions=r.wrong_assumptions,
            )
        )
    return compressed


def recount_from_prompts(results: list[SimulationResult]) -> None:
    """Replace heuristic input token counts with real tiktoken counts.

    For any round that has non-empty prompt_text, replace input_tokens
    with the actual BPE token count and mark token_source as 'measured'.
    Recomputes cumulative_tokens and result totals in-place.

    Output tokens remain estimated (no LLM response text available).
    """
    from metrics.token_counter import count_tokens

    for result in results:
        cumulative = 0
        for rd in result.rounds:
            if rd.prompt_text and rd.prompt_text.strip():
                rd.input_tokens = count_tokens(rd.prompt_text)
                rd.token_source = "measured"
            cumulative += rd.input_tokens + rd.output_tokens
            rd.cumulative_tokens = cumulative
        result.total_input_tokens = sum(r.input_tokens for r in result.rounds)
        result.total_output_tokens = sum(r.output_tokens for r in result.rounds)
        result.total_tokens = result.total_input_tokens + result.total_output_tokens


def run_simulation(
    task: str,
    operations: int,
    modes: list[str] | None = None,
    assumption_accuracy: float = 1.0,
) -> list[SimulationResult]:
    """Run simulations for selected modes.

    Args:
        task: The task description to simulate.
        operations: Number of operations the task requires.
        modes: List of mode names to simulate. Defaults to all modes.
        assumption_accuracy: Accuracy of assumptions for Assumption Led mode (0.0–1.0).

    Returns:
        List of SimulationResult objects.
    """
    from examples.catalog import get_optimized_prompt, get_prompt_for_mode

    if modes is None:
        modes = list(SIMULATION_MODES.keys())

    optimized = get_optimized_prompt(task)

    results = []
    for mode in modes:
        if mode in SIMULATION_MODES:
            if mode == "Assumption Led":
                result = _simulate_assumption_led(task, operations, assumption_accuracy)
            else:
                result = SIMULATION_MODES[mode](task, operations)
            result.optimized_prompt = optimized

            # Populate prompt texts from catalog
            prompt_data = get_prompt_for_mode(task, mode)
            if isinstance(prompt_data, list):
                for i, round_obj in enumerate(result.rounds):
                    if i < len(prompt_data):
                        round_obj.prompt_text = prompt_data[i]
                    else:
                        round_obj.prompt_text = (
                            f"(continued clarification round {i + 1})"
                        )
            elif isinstance(prompt_data, str):
                if result.rounds:
                    result.rounds[0].prompt_text = prompt_data

            # Populate assumptions list for Assumption Led mode
            if result.mode == "Assumption Led":
                if result.rounds and isinstance(prompt_data, list) and prompt_data:
                    result.rounds[0].assumptions = [prompt_data[0]]

            results.append(result)
    recount_from_prompts(results)
    return results

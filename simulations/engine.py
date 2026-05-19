"""Simulation engine for ICR Lab.

Generates synthetic interaction traces for different prompting modes,
showing how interaction architecture affects token consumption.
"""

import hashlib
from dataclasses import dataclass

import streamlit as st


@dataclass
class InteractionRound:
    """A single round of interaction between user and AI system."""

    round_number: int
    input_tokens: int
    output_tokens: int
    cumulative_tokens: int
    description: str
    prompt_text: str = ""


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


def _simulate(
    mode: str, task: str, operations: int, round_specs: list[tuple[float, float, str]]
) -> SimulationResult:
    return _build_result(mode, _base_tokens(task), operations, round_specs)


_OVER_COMPRESSED_ROUNDS = [
    (0.8, 0.6, "Over-compressed intent — system misinterprets scope"),
    (2.5, 1.5, "Correction: user explains what was missed"),
    (3.0, 2.0, "Re-correction: implicit constraints not captured"),
    (4.0, 2.5, "Full restatement with explicit ordering and dependencies"),
    (2.0, 2.0, "Final execution after accumulated corrections"),
]


# Mode registry
SIMULATION_MODES = {
    "Verbose Prompting": lambda t, ops: _simulate("Verbose Prompting", t, ops, _VERBOSE_ROUNDS),
    "Clarification Heavy": lambda t, ops: _simulate(
        "Clarification Heavy", t, ops, _clarification_rounds(t)
    ),
    "Context-Aware": lambda t, ops: _simulate("Context-Aware", t, ops, _CONTEXT_AWARE_ROUNDS),
    "Intent-Optimized": lambda t, ops: _simulate(
        "Intent-Optimized", t, ops, _INTENT_OPTIMIZED_ROUNDS
    ),
    "Over-Compressed": lambda t, ops: _simulate("Over-Compressed", t, ops, _OVER_COMPRESSED_ROUNDS),
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
            )
        )
    return compressed


@st.cache_data(show_spinner=False)
def run_simulation(
    task: str, operations: int, modes: list[str] | None = None
) -> list[SimulationResult]:
    """Run simulations for selected modes.

    Args:
        task: The task description to simulate.
        operations: Number of operations the task requires.
        modes: List of mode names to simulate. Defaults to all modes.

    Returns:
        List of SimulationResult objects.
    """
    from examples.catalog import get_optimized_prompt, get_prompt_for_mode  # noqa: PLC0415

    if modes is None:
        modes = list(SIMULATION_MODES.keys())

    optimized = get_optimized_prompt(task)

    results = []
    for mode in modes:
        if mode in SIMULATION_MODES:
            result = SIMULATION_MODES[mode](task, operations)
            result.optimized_prompt = optimized

            # Populate prompt texts from catalog
            prompt_data = get_prompt_for_mode(task, mode)
            if isinstance(prompt_data, list):
                for i, round_obj in enumerate(result.rounds):
                    if i < len(prompt_data):
                        round_obj.prompt_text = prompt_data[i]
                    else:
                        round_obj.prompt_text = f"(continued clarification round {i + 1})"
            elif isinstance(prompt_data, str) and result.rounds:
                result.rounds[0].prompt_text = prompt_data

            results.append(result)
    return results

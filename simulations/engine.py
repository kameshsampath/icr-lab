"""Simulation engine for ICR Lab.

Generates synthetic interaction traces for different prompting modes,
showing how interaction architecture affects token consumption.
"""

import hashlib
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
    # Use hash for deterministic variation + word count for scaling
    hash_val = int(hashlib.md5(task.encode()).hexdigest()[:8], 16)
    word_count = len(task.split())
    # Base complexity: 5-15 range
    return 5 + (hash_val % 6) + min(word_count // 3, 5)


def _base_tokens(task: str) -> int:
    """Base token count derived from task complexity."""
    complexity = _task_complexity(task)
    return complexity * 120


def simulate_verbose(task: str, operations: int) -> SimulationResult:
    """Verbose Prompting: large prompts with repeated explanations."""
    base = _base_tokens(task)
    rounds = []
    cumulative = 0

    # Round 1: massive initial prompt with full context
    r1_input = base * 8
    r1_output = base * 4
    cumulative += r1_input + r1_output
    rounds.append(InteractionRound(
        round_number=1,
        input_tokens=r1_input,
        output_tokens=r1_output,
        cumulative_tokens=cumulative,
        description="Full context dump with repeated explanations and examples",
    ))

    # Round 2: follow-up with re-stated context
    r2_input = base * 6
    r2_output = base * 3
    cumulative += r2_input + r2_output
    rounds.append(InteractionRound(
        round_number=2,
        input_tokens=r2_input,
        output_tokens=r2_output,
        cumulative_tokens=cumulative,
        description="Re-explained requirements with additional verbose context",
    ))

    total_input = sum(r.input_tokens for r in rounds)
    total_output = sum(r.output_tokens for r in rounds)

    return SimulationResult(
        mode="Verbose Prompting",
        rounds=rounds,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=total_input + total_output,
        operations_achieved=operations,
    )


def simulate_clarification(task: str, operations: int) -> SimulationResult:
    """Clarification Heavy: multiple interaction rounds with growing context."""
    base = _base_tokens(task)
    num_rounds = 5 + (_task_complexity(task) % 4)  # 5-8 rounds
    rounds = []
    cumulative = 0

    descriptions = [
        "Initial vague request",
        "Clarification: what exactly do you mean?",
        "Follow-up: which components specifically?",
        "More detail: what about dependencies?",
        "Confirmation: let me restate everything",
        "Adjustment: actually, also include...",
        "Final confirmation with full restated context",
        "Execution with accumulated context",
    ]

    for i in range(num_rounds):
        # Context grows each round (prior conversation included)
        context_growth = 1.0 + (i * 0.4)
        r_input = int(base * 1.5 * context_growth)
        r_output = int(base * 0.8)
        cumulative += r_input + r_output
        rounds.append(InteractionRound(
            round_number=i + 1,
            input_tokens=r_input,
            output_tokens=r_output,
            cumulative_tokens=cumulative,
            description=descriptions[min(i, len(descriptions) - 1)],
        ))

    total_input = sum(r.input_tokens for r in rounds)
    total_output = sum(r.output_tokens for r in rounds)

    return SimulationResult(
        mode="Clarification Heavy",
        rounds=rounds,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=total_input + total_output,
        operations_achieved=operations,
    )


def simulate_context_aware(task: str, operations: int) -> SimulationResult:
    """Context-Aware: partial context reuse with moderate efficiency."""
    base = _base_tokens(task)
    rounds = []
    cumulative = 0

    # Round 1: structured intent with some context
    r1_input = base * 3
    r1_output = base * 2
    cumulative += r1_input + r1_output
    rounds.append(InteractionRound(
        round_number=1,
        input_tokens=r1_input,
        output_tokens=r1_output,
        cumulative_tokens=cumulative,
        description="Structured request with relevant context",
    ))

    # Round 2: refinement with context delta only
    r2_input = int(base * 1.5)
    r2_output = int(base * 1.5)
    cumulative += r2_input + r2_output
    rounds.append(InteractionRound(
        round_number=2,
        input_tokens=r2_input,
        output_tokens=r2_output,
        cumulative_tokens=cumulative,
        description="Refinement using context references (not repetition)",
    ))

    # Round 3: confirmation with minimal overhead
    r3_input = base
    r3_output = int(base * 1.2)
    cumulative += r3_input + r3_output
    rounds.append(InteractionRound(
        round_number=3,
        input_tokens=r3_input,
        output_tokens=r3_output,
        cumulative_tokens=cumulative,
        description="Final execution with compressed context",
    ))

    total_input = sum(r.input_tokens for r in rounds)
    total_output = sum(r.output_tokens for r in rounds)

    return SimulationResult(
        mode="Context-Aware",
        rounds=rounds,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=total_input + total_output,
        operations_achieved=operations,
    )


def simulate_intent_optimized(task: str, operations: int) -> SimulationResult:
    """Intent-Optimized: compact semantic interaction, minimal tokens."""
    base = _base_tokens(task)
    rounds = []

    # Single round: compressed intent expression
    r_input = int(base * 1.2)
    r_output = int(base * 1.8)
    cumulative = r_input + r_output
    rounds.append(InteractionRound(
        round_number=1,
        input_tokens=r_input,
        output_tokens=r_output,
        cumulative_tokens=cumulative,
        description="Single compressed intent — system resolves dependency graph",
    ))

    return SimulationResult(
        mode="Intent-Optimized",
        rounds=rounds,
        total_input_tokens=r_input,
        total_output_tokens=r_output,
        total_tokens=cumulative,
        operations_achieved=operations,
    )


# Mode registry
SIMULATION_MODES = {
    "Verbose Prompting": simulate_verbose,
    "Clarification Heavy": simulate_clarification,
    "Context-Aware": simulate_context_aware,
    "Intent-Optimized": simulate_intent_optimized,
}


def run_simulation(task: str, operations: int, modes: list[str] | None = None) -> list[SimulationResult]:
    """Run simulations for selected modes.

    Args:
        task: The task description to simulate.
        operations: Number of operations the task requires.
        modes: List of mode names to simulate. Defaults to all modes.

    Returns:
        List of SimulationResult objects.
    """
    from examples.catalog import get_prompt_for_mode, get_optimized_prompt

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
                # Clarification mode: one prompt per round
                for i, round_obj in enumerate(result.rounds):
                    if i < len(prompt_data):
                        round_obj.prompt_text = prompt_data[i]
                    else:
                        round_obj.prompt_text = f"(continued clarification round {i + 1})"
            elif isinstance(prompt_data, str):
                # Single-prompt modes: assign to first round
                if result.rounds:
                    result.rounds[0].prompt_text = prompt_data

            results.append(result)
    return results

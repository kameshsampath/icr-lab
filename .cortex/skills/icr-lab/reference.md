# ICR Lab — Reference

## Intent Compression Ratio (ICR)

```
ICR = (Intent Fulfilled / Total Tokens) × 1000
```

**Intent Fulfilled** = number of discrete operations the AI system completes from a single interaction sequence.

**Total Tokens** = sum of all input + output tokens across all rounds of interaction.

## Simulation Modes

| Mode | Behavior | Typical ICR |
|------|----------|-------------|
| Verbose Prompting | Long prompts with repeated context, over-explanation | Low |
| Clarification Heavy | Multiple back-and-forth rounds, context grows each turn | Lowest |
| Context-Aware | Structured requests, partial context reuse | Medium |
| Intent-Optimized | Single compressed expression, system resolves deps | Highest |
| Over-Compressed | Too terse → triggers correction loops → amplifies tokens | Low-Medium |

## Key Insight

> Interaction architecture determines token economics more than output brevity.
> A 35% output compression saves less than switching from Clarification Heavy to Intent-Optimized.

## Token Amplification

```
Amplification = Mode Total Tokens / Best Mode Total Tokens
```

Clarification Heavy typically shows 4-8x amplification vs Intent-Optimized.

## Configuration

`icr-lab.toml` sections:
- `[backend]` — default backend selection
- `[backend.*]` — per-backend settings (owned by backends module + scaffold-backend skill)
- `[deploy]` — SiS deployment config (owned by deploy-sis skill)

## Backend Protocol

All backends implement `LLMBackend`:
- `complete(prompt, **kwargs) -> CompletionResult`
- `is_available() -> bool`
- `name: str`

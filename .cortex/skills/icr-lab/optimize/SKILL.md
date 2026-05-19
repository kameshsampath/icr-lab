---
name: icr-lab/optimize
description: Compress a verbose prompt to intent-optimized form
triggers:
  - optimize prompt
  - compress prompt
  - reduce tokens
  - intent optimize
---

# ICR Optimize

Transform a verbose or over-specified prompt into its intent-optimized equivalent.

## Workflow

1. Accept a verbose prompt from the user
2. Identify the core intent (what operations need to happen)
3. Strip redundant context, repeated instructions, over-explanation
4. Produce a compressed prompt that preserves all intent
5. Show before/after comparison with token estimates

## Optimization Rules

1. **Extract operations** — identify discrete actions the prompt requests
2. **Remove repetition** — same instruction said multiple ways → keep one
3. **Collapse context** — multi-paragraph background → single constraint line
4. **Implicit > explicit** — if the AI system can infer it, don't state it
5. **Preserve constraints** — ordering, dependencies, non-obvious requirements stay

## Anti-patterns (Over-Compression)

Do NOT compress so much that:
- Critical constraints are lost
- Ambiguity requires clarification rounds
- The system must guess intent

The sweet spot is Intent-Optimized, not Over-Compressed.

## Output Format

```markdown
### Original (Verbose)
> [original prompt]
> ~{word_count} words, est. {token_count} tokens

### Optimized
> [compressed prompt]
> ~{word_count} words, est. {token_count} tokens

### Reduction
- Words: {reduction}%
- Estimated tokens: {reduction}%
- Operations preserved: {count}/{count}
```

## Using a Live Backend

If a live backend (cortex or lmstudio) is available, use it to:
1. Generate the optimized version via LLM
2. Validate the optimized prompt produces equivalent output
3. Measure actual token counts from the API response

"""Help & Glossary page for ICR Lab."""

import streamlit as st

col_title, col_nav = st.columns([4, 1])
with col_title:
    st.header("Help & Glossary")
with col_nav:
    st.page_link("pages/home.py", label="Home", icon="🏠")
st.markdown(
    "ICR Lab uses a few terms from AI systems, developer experience, and observability. "
    "This page explains them in practical terms."
)

st.divider()

# --- Terms ---

st.subheader("Intent Compression Ratio")
st.markdown(
    "Intent Compression Ratio, or ICR, measures how much useful intent is fulfilled per token consumed."
)
st.markdown("In this app:")
st.latex(
    r"\text{ICR} = \frac{\text{Intent Fulfilled}}{\text{Total Tokens}} \times 1000"
)
st.markdown(
    "Higher ICR means the system achieves the same useful outcome with fewer tokens."
)

st.divider()

st.subheader("Token")
st.markdown(
    "A token is a unit of text processed by a language model. Tokens are usually smaller than words, "
    "but not always. Token count matters because LLM cost, latency, and context usage are often tied to tokens."
)

st.divider()

st.subheader("Token Economics")
st.markdown(
    "Token economics refers to the cost, latency, and infrastructure impact of the tokens "
    "consumed during AI interactions."
)

st.divider()

st.subheader("Token Amplification")
st.markdown(
    "Token amplification happens when a small human intent expands into a much larger machine "
    "interaction because of repeated context, clarification loops, verbose prompts, or inefficient orchestration."
)

st.divider()

st.subheader("Token Amplification Factor")
st.markdown(
    "Token Amplification Factor compares each mode's total token usage against the most efficient selected mode."
)
st.markdown("**Formula:**")
st.latex(
    r"\text{Token Amplification Factor} = \frac{\text{Mode Total Tokens}}{\text{Lowest Total Tokens Across Selected Modes}}"
)
st.markdown(
    "A 7.0x amplification factor means that mode used seven times more tokens "
    "than the most efficient mode for the same intent."
)

st.divider()

st.subheader("Interaction Architecture")
st.markdown(
    "Interaction architecture describes how a user's intent flows through an AI system."
)
st.markdown("Examples in this app:")
st.markdown(
    "- Verbose Prompting\n- Clarification Heavy\n- Context-Aware\n- Intent-Optimized"
)

st.divider()

st.subheader("Verbose Prompting")
st.markdown(
    "Verbose prompting relies on long, detailed prompts to compensate for missing context "
    "or weak system understanding. It often increases token usage."
)

st.divider()

st.subheader("Clarification Heavy")
st.markdown(
    "Clarification-heavy workflows require multiple back-and-forth interactions before the system "
    "can complete the task. Each round adds more tokens."
)

st.divider()

st.subheader("Context-Aware")
st.markdown(
    "A context-aware system can reuse some previous or environmental context. This reduces "
    "repeated explanation and usually improves token efficiency."
)

st.divider()

st.subheader("Intent-Optimized")
st.markdown(
    "An intent-optimized interaction captures the user's goal in a compact, structured, "
    "reusable form. The system needs fewer tokens to understand and act."
)

st.divider()

st.subheader("Over-Compressed")
st.markdown(
    "Over-compressed prompts strip so much context that the system misinterprets the intent. "
    "This triggers correction rounds that often consume more tokens than a moderately verbose "
    "prompt would have. High compression only works when the receiver has enough shared context "
    "to decompress accurately."
)

st.divider()

st.subheader("Output Compression")
st.markdown(
    "Output compression reduces the verbosity of AI responses without losing technical accuracy. "
    "Tools like [Caveman](https://github.com/juliusbrussee/caveman) achieve ~65% output token reduction. "
    "ICR Lab lets you simulate this to show that output compression compounds with good interaction "
    "architecture but does not replace it. The architecture gap often *widens* with compression because "
    "efficient modes have a higher output-to-input ratio and benefit more."
)

st.divider()

st.subheader("Intent Fulfilled")
st.markdown(
    "Intent fulfilled is a simplified score used by the simulation to represent "
    "how much useful work the system completed."
)

st.divider()

st.subheader("Relative ICR Score")
st.markdown(
    "Relative ICR Score normalizes ICR values against the most efficient mode in the "
    "current simulation. The top mode shows 100% as a relative baseline, not as a claim of perfection."
)

st.divider()

st.subheader("Simulation Mode")
st.markdown(
    "Simulation mode means the app uses synthetic traces instead of live LLM calls. "
    "This keeps v1 deterministic, reproducible, free to run, and focused on the concept."
)

st.divider()

# --- Why no live LLM ---

st.header("Why no live LLM in v1?")
st.markdown(
    "ICR Lab v1 uses simulation instead of live model calls because the goal is to explain "
    "interaction architecture, not benchmark models."
)
st.markdown("A deterministic simulation makes the demo:")
st.markdown(
    "- Easier to reproduce\n"
    "- Free to run\n"
    "- Simpler to deploy\n"
    "- Easier to reason about\n"
    "- Focused on token behavior rather than model quality"
)
st.markdown("Live model integrations can be added later as optional adapters.")

st.divider()

# --- Relevant Links ---

st.header("Relevant Links")
st.markdown(
    "- [ICR Lab GitHub repo](https://github.com/kameshsampath/icr-lab)\n"
    "- [Live app](https://icr-lab.streamlit.app/)\n"
    "- [ICR: Measuring the Power of Intent](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9)\n"
    "- [Caveman](https://github.com/juliusbrussee/caveman) — output token compression for AI agents\n"
    "- [Streamlit documentation](https://docs.streamlit.io/)\n"
    "- [Streamlit Community Cloud](https://streamlit.io/cloud)\n"
    "- [Snowflake Cortex documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions) "
    "— possible future live-model backend (not a v1 dependency)"
)

st.divider()

# --- Related Reading ---

st.header("Related Reading")
st.markdown(
    "These essays provide the broader context behind ICR Lab and the idea of intent-native software systems."
)
st.markdown(
    "- [Infrastructure as Intent: The Field Velocity Blueprint]"
    "(https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14)\n"
    "- [The Ghost in the Machine: Why AI Needs the Spirit of UML]"
    "(https://blogs.kameshs.dev/the-ghost-in-the-machine-why-ai-needs-the-spirit-of-uml-0d8864e583e2)\n"
    "- [Intent Driven Development: The Shift Developers Can't Ignore]"
    "(https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c)\n"
    "- [Intent Compression Ratio: Measuring the Power of Intent]"
    "(https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9)"
)

st.divider()
st.page_link("pages/home.py", label="← Back to Home", icon="🏠")

# ICR Lab — Examples Guide

This document provides worked examples showing how the same task can be expressed at different intent compression levels, and how that impacts token usage.

## How to Read ICR Scores

| ICR Score | Meaning |
|-----------|---------|
| 0–10 | Low compression — high token waste |
| 10–30 | Moderate — room for improvement |
| 30–60 | Good — structured intent expression |
| 60–100 | Excellent — maximum compression |

**Token Amplification Factor** shows how many times more tokens a mode uses compared to the optimal. An amplification of `5.0x` means 5 times more tokens than necessary.

---

## Example 1: Deploy a Connector with Snowflake Openflow

**Operations compressed:** 12 (create service user, role, grants, network rule, network policy, attach policy, auth policy, attach auth policy, PAT constraints, generate PAT, store PAT, validate)

**ICR = 12 ops / 1 intent**

### Verbose Prompting (ICR ~3)

> I need to deploy a connector using Snowflake Openflow. First, I need a service user created in Snowflake. The user should be a service account type. Then I need a role created for this service user. The role should be granted to the user. After that, I need network rules configured to allow access to the external endpoint. The network rule should be wrapped in a network policy. The network policy needs to be attached to the service user. Then I need an authentication policy that references the correct role. The auth policy also needs to be attached to the user. After all of that, I need PAT policy constraints configured, and then a programmatic access token generated. The PAT should be stored securely. Finally, validate the token works with NiPyAPI. Please make sure each step is done in the correct order because the dependencies matter.

**Problem:** Repeats ordering constraints the system already knows. Restates obvious relationships. ~180 tokens input.

### Clarification Heavy (ICR ~4)

> Round 1: "Can you help me set up Openflow?"
> Round 2: "It's a Snowflake connector. I need to deploy one."
> Round 3: "It connects to Google Cloud Storage."
> Round 4: "I think I need a PAT for authentication."
> Round 5: "Yes, there should be network policies too."
> ...

**Problem:** Each round re-sends the full conversation history. Context grows ~40% per round. 5-8 rounds accumulate significant token waste.

### Context-Aware (ICR ~6)

> Deploy a Snowflake Openflow connector to GCS. Set up the service user with appropriate network and auth policies, then generate a PAT for NiPyAPI client authentication.

**Improvement:** References concepts without over-explaining. Trusts the system to resolve dependency ordering.

### Intent-Optimized (ICR ~21)

> Deploy Openflow connector: GCS target, PAT auth, NiPyAPI client.

**Why it works:** Specifies the three key parameters (target, auth method, client) and trusts the system to execute the full dependency graph. The system has high ICR — it absorbs 12 operations from 1 compact intent.

---

## Example 2: Deploy Payment Service

**Operations compressed:** 9

### Verbose (~180 tokens)
> I need to deploy our payment service. It's a containerized application that needs to be deployed to Kubernetes. First, build the Docker image...

### Intent-Optimized (~15 tokens)
> Deploy payment-service: k8s, HPA 2-10, full observability (metrics/dashboards/alerts/tracing).

**Savings:** ~85% token reduction, same outcome.

---

## Example 3: Set Up Iceberg Table

**Operations compressed:** 6

### Verbose (~140 tokens)
> I want to set up an Apache Iceberg table in Snowflake that uses an external volume. First, I need a storage integration created that points to our S3 bucket...

### Intent-Optimized (~12 tokens)
> Iceberg table: ANALYTICS db, S3 external volume (us-east-1), validate access.

**Savings:** ~80% token reduction.

---

## Example 4: Build CDC Pipeline

**Operations compressed:** 10

### Verbose (~200 tokens)
> I need to build a real-time data pipeline using Change Data Capture. The source is a PostgreSQL database...

### Intent-Optimized (~14 tokens)
> CDC pipeline: Postgres → Kafka (Avro) → warehouse. Transforms, DLQ, monitoring, backfill.

**Savings:** ~88% token reduction.

---

## Tips for Writing Intent-Optimized Prompts

1. **Name the pattern, don't describe it** — "OAuth2 authz code + PKCE" beats explaining the entire flow
2. **Specify only the parameters that differentiate** — target, auth method, constraints
3. **Trust the system's graph resolution** — don't restate dependency ordering
4. **Use structured shorthand** — colons, arrows, parenthetical constraints
5. **Omit what's standard** — if every deployment needs health checks, don't mention them
6. **Front-load the action verb** — "Deploy", "Configure", "Migrate"

## The Pattern

```
[Action] [Target]: [Key Param 1], [Key Param 2], [Constraints].
```

Examples:
- `Deploy Openflow connector: GCS target, PAT auth, NiPyAPI client.`
- `Iceberg table: ANALYTICS db, S3 external volume (us-east-1), validate access.`
- `CDC pipeline: Postgres → Kafka (Avro) → warehouse. Transforms, DLQ, monitoring, backfill.`
- `Network access: allow googleapis.com for service user, validate.`

---

## Running These Examples

```bash
uv run icr-lab
```

Select any example task from the sidebar dropdown to see the full simulation with prompt comparisons.

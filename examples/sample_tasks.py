"""Pre-built example tasks for ICR Lab simulations."""

SAMPLE_TASKS = [
    "Deploy a connector with Snowflake Openflow",
    "Deploy payment service with autoscaling and observability",
    "Set up an Iceberg table with external volume",
    "Refactor authentication module to use OAuth2",
    "Build real-time data pipeline with CDC",
    "Configure network access with security policies",
    "Deploy microservices app with service mesh and canary rollouts",
    "Implement a rate limiter with sliding window and distributed state",
    "Provision multi-region AWS infrastructure with DR failover",
    "Configure hardened Linux fleet with CIS benchmarks and monitoring",
]

# Mapping of tasks to their estimated operation counts
# (used to derive complexity for simulation)
TASK_OPERATIONS = {
    "Deploy a connector with Snowflake Openflow": 12,
    "Deploy payment service with autoscaling and observability": 9,
    "Set up an Iceberg table with external volume": 6,
    "Refactor authentication module to use OAuth2": 8,
    "Build real-time data pipeline with CDC": 10,
    "Configure network access with security policies": 4,
    "Deploy microservices app with service mesh and canary rollouts": 11,
    "Implement a rate limiter with sliding window and distributed state": 8,
    "Provision multi-region AWS infrastructure with DR failover": 10,
    "Configure hardened Linux fleet with CIS benchmarks and monitoring": 9,
}


def get_operations_count(task: str) -> int:
    """Estimate the number of operations for a given task."""
    if task in TASK_OPERATIONS:
        return TASK_OPERATIONS[task]
    # Heuristic: estimate based on word count and action verbs
    words = task.split()
    action_words = {
        "deploy",
        "configure",
        "set",
        "build",
        "create",
        "migrate",
        "refactor",
        "implement",
        "integrate",
        "setup",
        "install",
    }
    action_count = sum(1 for w in words if w.lower() in action_words)
    return max(3, len(words) // 2 + action_count * 2)

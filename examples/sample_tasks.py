"""Pre-built example tasks for ICR Lab simulations."""

from pathlib import Path

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
    "Create a Snowflake Native App with versioned data sharing",
    "Set up Cortex ML functions for sentiment analysis pipeline",
    "Configure Snowflake dynamic tables with incremental refresh",
    "Deploy a Snowpark Container Services job with GPU compute",
    "Build a Snowflake data mesh with governance policies",
]

# Verbose tasks loaded from files in examples/verbose/
_VERBOSE_DIR = Path(__file__).parent / "verbose"


def load_verbose_tasks() -> list[dict[str, str]]:
    """Load verbose task examples from .md/.txt files in examples/verbose/."""
    tasks = []
    if _VERBOSE_DIR.exists():
        for f in sorted(_VERBOSE_DIR.glob("*")):
            if f.suffix in (".md", ".txt"):
                label = f"[Verbose] {f.stem.replace('-', ' ').title()}"
                tasks.append({"label": label, "text": f.read_text().strip(), "path": str(f)})
    return tasks


VERBOSE_TASKS = load_verbose_tasks()

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
    "Create a Snowflake Native App with versioned data sharing": 11,
    "Set up Cortex ML functions for sentiment analysis pipeline": 7,
    "Configure Snowflake dynamic tables with incremental refresh": 8,
    "Deploy a Snowpark Container Services job with GPU compute": 10,
    "Build a Snowflake data mesh with governance policies": 12,
}


def get_operations_count(task: str) -> int:
    """Estimate the number of operations for a given task."""
    if task in TASK_OPERATIONS:
        return TASK_OPERATIONS[task]
    # Heuristic: estimate based on word count and action verbs
    words = task.split()
    action_words = {"deploy", "configure", "set", "build", "create", "migrate",
                    "refactor", "implement", "integrate", "setup", "install"}
    action_count = sum(1 for w in words if w.lower() in action_words)
    return max(3, len(words) // 2 + action_count * 2)

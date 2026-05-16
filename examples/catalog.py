"""Prompt examples catalog for ICR Lab.

Provides concrete prompt examples for each simulation mode,
showing how the same intent can be expressed at different
compression levels.
"""

EXAMPLES = [
    {
        "task": "Deploy a connector with Snowflake Openflow",
        "operations": [
            "Create service user",
            "Create service role",
            "Grant role to user",
            "Create network rule",
            "Create network policy",
            "Attach network policy to user",
            "Create authentication policy",
            "Attach authentication policy to user",
            "Configure PAT policy constraints",
            "Generate PAT",
            "Store PAT securely for client usage",
            "Validate token exchange via Apache NiPyAPI",
        ],
        "prompts": {
            "Verbose Prompting": (
                "I need to deploy a connector using Snowflake Openflow. "
                "First, I need a service user created in Snowflake. The user should be a service account type. "
                "Then I need a role created for this service user. The role should be granted to the user. "
                "After that, I need network rules configured to allow access to the external endpoint. "
                "The network rule should be wrapped in a network policy. The network policy needs to be "
                "attached to the service user. Then I need an authentication policy that references the "
                "correct role. The auth policy also needs to be attached to the user. After all of that, "
                "I need PAT policy constraints configured, and then a programmatic access token generated. "
                "The PAT should be stored securely. Finally, validate the token works with NiPyAPI. "
                "Please make sure each step is done in the correct order because the dependencies matter. "
                "The network policy must exist before it's attached. The auth policy must reference the "
                "correct role. The PAT must be generated after all constraints are satisfied."
            ),
            "Clarification Heavy": [
                "Can you help me set up Openflow?",
                "It's a Snowflake connector. I need to deploy one.",
                "It connects to Google Cloud Storage.",
                "I think I need a PAT for authentication.",
                "Yes, there should be network policies too.",
                "The service user needs the right role and policies attached.",
                "OK, and the PAT needs to be generated last, after everything else is configured.",
                "Right, go ahead and set it all up in the correct order.",
            ],
            "Context-Aware": (
                "Deploy a Snowflake Openflow connector to GCS. "
                "Set up the service user with appropriate network and auth policies, "
                "then generate a PAT for NiPyAPI client authentication."
            ),
            "Intent-Optimized": (
                "Deploy Openflow connector: GCS target, PAT auth, NiPyAPI client."
            ),
        },
    },
    {
        "task": "Deploy payment service with autoscaling and observability",
        "operations": [
            "Build container image",
            "Push to registry",
            "Create Kubernetes deployment",
            "Configure HPA autoscaling",
            "Set up service and ingress",
            "Deploy Prometheus metrics exporter",
            "Configure Grafana dashboards",
            "Set up alerting rules",
            "Configure distributed tracing",
        ],
        "prompts": {
            "Verbose Prompting": (
                "I need to deploy our payment service. It's a containerized application that needs to "
                "be deployed to Kubernetes. First, build the Docker image from the Dockerfile in the "
                "repo. Then push it to our container registry. Create a Kubernetes deployment with the "
                "image. I also need autoscaling — use a Horizontal Pod Autoscaler that scales based on "
                "CPU and memory. Set up a Service and Ingress so it's accessible. For observability, "
                "I need Prometheus metrics exported from the service, Grafana dashboards configured to "
                "show payment transaction metrics, alerting rules for error rates and latency, and "
                "distributed tracing with Jaeger. Make sure the deployment has proper resource limits "
                "and health checks configured. The autoscaler should scale between 2 and 10 replicas."
            ),
            "Clarification Heavy": [
                "I need to deploy the payment service.",
                "Yes, to Kubernetes. It needs autoscaling.",
                "HPA based on CPU and memory. Min 2, max 10 replicas.",
                "Also need observability. Prometheus and Grafana.",
                "Yes, and alerting. Plus tracing with Jaeger.",
                "The image needs to be built and pushed first.",
            ],
            "Context-Aware": (
                "Deploy payment-service to k8s with HPA (2-10 pods, CPU/memory). "
                "Include full observability stack: Prometheus metrics, Grafana dashboards, "
                "alerting rules, and Jaeger tracing."
            ),
            "Intent-Optimized": (
                "Deploy payment-service: k8s, HPA 2-10, full observability (metrics/dashboards/alerts/tracing)."
            ),
        },
    },
    {
        "task": "Set up an Iceberg table with external volume",
        "operations": [
            "Create storage integration",
            "Configure IAM roles",
            "Create external volume",
            "Validate access",
            "Create catalog integration",
            "Create Iceberg table",
        ],
        "prompts": {
            "Verbose Prompting": (
                "I want to set up an Apache Iceberg table in Snowflake that uses an external volume. "
                "First, I need a storage integration created that points to our S3 bucket. "
                "The S3 bucket is in us-east-1. I'll need the IAM role configured with the right "
                "trust policy so Snowflake can assume it. Then create an external volume using the "
                "storage integration. Make sure to validate that Snowflake can actually access the "
                "bucket by checking the storage integration properties and doing a test. Then set up "
                "a catalog integration if needed. Finally, create the Iceberg table using the external "
                "volume as storage. The table should be in my analytics database."
            ),
            "Clarification Heavy": [
                "I need an Iceberg table.",
                "On S3. In us-east-1.",
                "I need an external volume for it.",
                "The IAM role? Let me check... yes, I'll need a trust policy.",
                "The table goes in the analytics database.",
                "And yes, validate access works before creating the table.",
            ],
            "Context-Aware": (
                "Create Iceberg table in ANALYTICS db backed by external volume on S3 (us-east-1). "
                "Handle storage integration, IAM, and access validation."
            ),
            "Intent-Optimized": (
                "Iceberg table: ANALYTICS db, S3 external volume (us-east-1), validate access."
            ),
        },
    },
    {
        "task": "Refactor authentication module to use OAuth2",
        "operations": [
            "Audit current auth implementation",
            "Design OAuth2 flow",
            "Implement token endpoint",
            "Add refresh token logic",
            "Update middleware",
            "Migrate session handling",
            "Update API clients",
            "Add PKCE support",
        ],
        "prompts": {
            "Verbose Prompting": (
                "I need to refactor our authentication module. Currently it uses session-based auth "
                "with cookies, but we need to move to OAuth2. I need you to first audit the current "
                "implementation to understand all the places auth is used. Then design the OAuth2 flow — "
                "we want authorization code flow with PKCE. Implement a token endpoint that issues "
                "access and refresh tokens. Add logic for refresh token rotation. Update the auth "
                "middleware to validate JWT tokens instead of sessions. Migrate the session handling "
                "to use the new token-based approach. Update all API clients that currently send "
                "session cookies to use Bearer tokens instead. Make sure PKCE is implemented properly "
                "for public clients."
            ),
            "Clarification Heavy": [
                "We need to update our auth.",
                "Moving from sessions to OAuth2.",
                "Authorization code flow.",
                "Yes, with PKCE for public clients.",
                "Refresh tokens too, with rotation.",
                "All API clients need updating.",
                "The middleware needs to validate JWTs now.",
            ],
            "Context-Aware": (
                "Refactor auth from session-based to OAuth2 (authorization code + PKCE). "
                "Implement token endpoint with refresh rotation, update middleware to JWT validation, "
                "and migrate all API clients to Bearer tokens."
            ),
            "Intent-Optimized": (
                "Refactor auth → OAuth2: authz code + PKCE, JWT middleware, refresh rotation, migrate clients."
            ),
        },
    },
    {
        "task": "Build real-time data pipeline with CDC",
        "operations": [
            "Configure source database CDC",
            "Set up Kafka Connect source connector",
            "Create Kafka topics with schemas",
            "Implement stream processing transforms",
            "Configure sink connector",
            "Set up schema registry",
            "Implement dead letter queue",
            "Configure monitoring",
            "Set up data quality checks",
            "Implement backfill strategy",
        ],
        "prompts": {
            "Verbose Prompting": (
                "I need to build a real-time data pipeline using Change Data Capture. The source is "
                "a PostgreSQL database. I need CDC enabled on the source tables — use logical "
                "replication. Then set up a Kafka Connect source connector to stream the changes "
                "into Kafka. Create the necessary Kafka topics with proper partitioning and retention. "
                "Register Avro schemas in the schema registry. Implement stream processing to transform "
                "the CDC events — we need to denormalize some tables and compute aggregates. "
                "Set up a sink connector to write to the target data warehouse. Implement a dead letter "
                "queue for failed records. Add monitoring for lag, throughput, and errors. Set up data "
                "quality checks at the sink. Also implement a backfill strategy for the initial load "
                "and for cases where we need to replay events."
            ),
            "Clarification Heavy": [
                "I need a CDC pipeline.",
                "Source is PostgreSQL.",
                "Target is our data warehouse.",
                "Using Kafka for streaming.",
                "Yes, with schema registry. Avro format.",
                "Need transforms — denormalization and aggregates.",
                "Also need DLQ and monitoring.",
                "And a backfill strategy for initial load.",
            ],
            "Context-Aware": (
                "Build CDC pipeline: PostgreSQL → Kafka (Avro/Schema Registry) → warehouse. "
                "Include stream transforms (denorm + aggregates), DLQ, monitoring, "
                "and backfill strategy."
            ),
            "Intent-Optimized": (
                "CDC pipeline: Postgres → Kafka (Avro) → warehouse. Transforms, DLQ, monitoring, backfill."
            ),
        },
    },
    {
        "task": "Configure network access with security policies",
        "operations": [
            "Define network rule",
            "Create network policy",
            "Attach policy to account/user",
            "Validate connectivity",
        ],
        "prompts": {
            "Verbose Prompting": (
                "I need to configure network access in Snowflake. I want to create a network rule "
                "that allows access to googleapis.com. The rule should be of type HOST_PORT. Then I "
                "need a network policy that uses this rule in its allowed list. The policy should be "
                "attached to the service user we created. After attaching, I need to validate that "
                "the connectivity actually works by testing from the service account context. Make sure "
                "the rule is created before the policy references it, and the policy exists before "
                "it's attached to the user."
            ),
            "Clarification Heavy": [
                "I need network access configured.",
                "To googleapis.com.",
                "It's for a service user.",
                "A network policy with a rule, yes. HOST_PORT type.",
            ],
            "Context-Aware": (
                "Configure network access to googleapis.com for the service user. "
                "Create HOST_PORT rule, wrap in policy, attach to user, validate."
            ),
            "Intent-Optimized": (
                "Network access: allow googleapis.com for service user, validate."
            ),
        },
    },
    {
        "task": "Deploy microservices app with service mesh and canary rollouts",
        "operations": [
            "Create namespace with labels",
            "Deploy microservice Deployments",
            "Create ClusterIP Services",
            "Install Istio sidecar injection",
            "Configure VirtualService routing",
            "Define DestinationRules with subsets",
            "Set canary weight-based traffic split",
            "Enable mTLS with PeerAuthentication",
            "Add circuit breaker policies",
            "Configure rate limiting with EnvoyFilter",
            "Set up HPA for each service",
        ],
        "prompts": {
            "Verbose Prompting": (
                "I need to deploy our microservices application to Kubernetes with a service mesh. "
                "First, create a namespace with the proper Istio injection labels. Then deploy each "
                "microservice as a Deployment with the right resource limits and readiness probes. "
                "Create ClusterIP Services for each. Install Istio sidecar injection so all pods get "
                "Envoy proxies. Now configure VirtualService routing rules so traffic flows correctly "
                "between services. Define DestinationRules with subsets for stable and canary versions. "
                "Set up a canary rollout with weight-based traffic splitting — start at 10% canary. "
                "Enable mutual TLS between all services using PeerAuthentication. Add circuit breaker "
                "policies on the DestinationRules to handle failures gracefully. Configure rate limiting "
                "using an EnvoyFilter. Finally, set up Horizontal Pod Autoscalers for each service "
                "based on CPU utilization. Make sure Istio is injecting sidecars before you configure "
                "any mesh policies."
            ),
            "Clarification Heavy": [
                "I need to deploy microservices to Kubernetes.",
                "Yes, with a service mesh. Istio.",
                "We want canary deployments. Weight-based.",
                "Start at 10% traffic to canary.",
                "mTLS between services, yes.",
                "Also circuit breakers and rate limiting.",
                "Each service needs autoscaling too.",
                "HPA on CPU. Default thresholds are fine.",
            ],
            "Context-Aware": (
                "Deploy microservices to k8s with Istio mesh. Configure canary rollouts "
                "(10% initial weight), mTLS, circuit breakers, rate limiting, and HPA per service."
            ),
            "Intent-Optimized": (
                "Microservices on k8s: Istio mesh, canary 10%, mTLS, circuit breakers, rate limits, HPA."
            ),
        },
    },
    {
        "task": "Implement a rate limiter with sliding window and distributed state",
        "operations": [
            "Design sliding window algorithm",
            "Implement token bucket core",
            "Add sliding window counter with timestamps",
            "Integrate Redis as distributed backend",
            "Handle race conditions with Lua atomics",
            "Add middleware hook for HTTP frameworks",
            "Emit rate limit metrics (allowed/rejected/remaining)",
            "Write unit and integration tests",
        ],
        "prompts": {
            "Verbose Prompting": (
                "I need to implement a rate limiter for our API. It should use a sliding window "
                "algorithm, not a fixed window, so we don't get burst issues at window boundaries. "
                "Start by designing the sliding window approach — I'm thinking a hybrid of fixed "
                "window counters with interpolation. Implement the core token bucket logic first. "
                "Then add the sliding window counter that tracks request timestamps. The state needs "
                "to be distributed, so integrate Redis as the backend store. We'll have multiple "
                "instances of the service running, so there will be race conditions — use Redis Lua "
                "scripts to make the check-and-increment atomic. Expose this as a middleware that "
                "any HTTP handler can use. The middleware should set X-RateLimit headers. Add metrics "
                "emission so we can track allowed, rejected, and remaining quota in our monitoring. "
                "Write both unit tests for the algorithm and integration tests against a real Redis."
            ),
            "Clarification Heavy": [
                "I need a rate limiter.",
                "Sliding window, not fixed.",
                "Distributed — multiple service instances.",
                "Using Redis for shared state.",
                "Need to handle race conditions. Lua scripts.",
                "It should work as HTTP middleware.",
                "Yes, with X-RateLimit headers.",
                "And we need tests — unit and integration.",
            ],
            "Context-Aware": (
                "Implement distributed rate limiter: sliding window algorithm, Redis backend "
                "with Lua atomics for concurrency, HTTP middleware with X-RateLimit headers, "
                "metrics emission, unit + integration tests."
            ),
            "Intent-Optimized": (
                "Rate limiter: sliding window, Redis + Lua atomics, HTTP middleware, metrics, tests."
            ),
        },
    },
    {
        "task": "Provision multi-region AWS infrastructure with DR failover",
        "operations": [
            "Define provider configs for both regions",
            "Create VPCs with subnets per region",
            "Set up RDS primary with cross-region read replica",
            "Configure Route53 health checks",
            "Set up Route53 failover routing policy",
            "Create S3 buckets with cross-region replication",
            "Configure CloudFront with multi-origin failover",
            "Create IAM roles and policies",
            "Extract reusable Terraform modules",
            "Configure remote state with DynamoDB locking",
        ],
        "prompts": {
            "Verbose Prompting": (
                "I need to provision multi-region infrastructure on AWS using Terraform. We need "
                "disaster recovery with automatic failover. First, define provider configurations "
                "for us-east-1 (primary) and us-west-2 (DR). Create a VPC in each region with "
                "public and private subnets across multiple AZs. Set up an RDS PostgreSQL instance "
                "in the primary region with a cross-region read replica in DR. Configure Route53 "
                "health checks that monitor the primary region's endpoints. Set up a failover "
                "routing policy so traffic automatically goes to DR if primary is unhealthy. Create "
                "S3 buckets in both regions with cross-region replication enabled. Set up CloudFront "
                "with an origin group that fails over to the DR region. Create all necessary IAM "
                "roles and policies with least-privilege access. Extract common patterns into "
                "reusable Terraform modules. Use S3 backend with DynamoDB locking for state. "
                "Make sure the modules are parameterized so we can add more regions later."
            ),
            "Clarification Heavy": [
                "I need multi-region infra on AWS.",
                "For disaster recovery. Automatic failover.",
                "Primary is us-east-1, DR is us-west-2.",
                "Using Terraform.",
                "RDS Postgres with a cross-region replica.",
                "Route53 for DNS failover, yes.",
                "S3 needs cross-region replication too.",
                "And CloudFront in front with origin failover.",
                "Remote state in S3 with DynamoDB locking.",
            ],
            "Context-Aware": (
                "Terraform multi-region AWS (us-east-1 primary, us-west-2 DR): VPCs, RDS with "
                "cross-region replica, Route53 failover, S3 CRR, CloudFront origin groups, "
                "IAM least-privilege. Modularized with S3+DynamoDB state backend."
            ),
            "Intent-Optimized": (
                "Terraform: multi-region AWS DR (east-1/west-2), RDS replica, Route53 failover, S3 CRR, CloudFront, modular."
            ),
        },
    },
    {
        "task": "Configure hardened Linux fleet with CIS benchmarks and monitoring",
        "operations": [
            "Create Ansible inventory with host groups",
            "Write SSH hardening role (disable root, key-only auth)",
            "Apply CIS Level 1 benchmark tasks (kernel params, filesystem)",
            "Configure firewalld/iptables rules",
            "Deploy Prometheus node_exporter",
            "Configure Filebeat for centralized logging",
            "Set up unattended security upgrades",
            "Create users with sudo rules (no NOPASSWD)",
            "Run OpenSCAP compliance scan and generate report",
        ],
        "prompts": {
            "Verbose Prompting": (
                "I need to configure our Linux server fleet using Ansible to meet security "
                "requirements. First, create an inventory file that groups hosts by role — web "
                "servers, app servers, and databases. Write a hardening role that disables root "
                "SSH login, enforces key-only authentication, sets idle timeout, and disables "
                "password auth. Apply CIS Level 1 benchmark tasks — things like setting kernel "
                "parameters (disable IP forwarding, enable ASLR), restricting filesystem mounts, "
                "setting proper permissions on sensitive files. Configure firewall rules using "
                "firewalld — only allow necessary ports per host group. Deploy Prometheus "
                "node_exporter on all hosts for metrics collection. Set up Filebeat to ship logs "
                "to our ELK stack. Configure unattended security upgrades so critical patches "
                "apply automatically. Create operator users with proper sudo rules — no NOPASSWD, "
                "require password for privilege escalation. Finally, run an OpenSCAP compliance "
                "scan to validate everything and generate an HTML report. The playbook should be "
                "idempotent so we can run it repeatedly."
            ),
            "Clarification Heavy": [
                "I need to harden our Linux servers.",
                "Using Ansible. About 50 hosts.",
                "CIS benchmarks — Level 1.",
                "SSH hardening, kernel params, filesystem restrictions.",
                "Also need monitoring. Prometheus node_exporter.",
                "Logging too — Filebeat to ELK.",
                "Unattended security upgrades, yes.",
                "And run a compliance scan at the end. OpenSCAP.",
            ],
            "Context-Aware": (
                "Ansible playbook for Linux fleet hardening: CIS Level 1 benchmarks, SSH lockdown, "
                "firewalld rules by host group, node_exporter + Filebeat agents, unattended upgrades, "
                "operator users with sudo, OpenSCAP compliance scan."
            ),
            "Intent-Optimized": (
                "Ansible: CIS L1 hardening, SSH lockdown, firewalld, node_exporter, Filebeat, auto-patches, OpenSCAP report."
            ),
        },
    },
]


def get_example(task: str) -> dict | None:
    """Look up a full example by task description."""
    for example in EXAMPLES:
        if example["task"] == task:
            return example
    return None


def get_optimized_prompt(task: str) -> str:
    """Get the intent-optimized prompt for a task.

    Returns the catalog version if available, otherwise generates
    a synthetic compressed version.
    """
    example = get_example(task)
    if example:
        return example["prompts"]["Intent-Optimized"]

    # Synthetic generation for custom tasks
    words = task.split()
    # Keep action verbs and key nouns, drop filler
    filler = {"the", "a", "an", "with", "and", "to", "for", "in", "on", "of", "that", "is", "be"}
    key_words = [w for w in words if w.lower() not in filler]
    return " ".join(key_words[:8]) + ("." if len(key_words) > 0 else "")


def get_verbose_prompt(task: str) -> str:
    """Get the verbose prompt for a task.

    Returns the catalog version if available, otherwise generates
    a synthetic verbose version.
    """
    example = get_example(task)
    if example:
        prompt = example["prompts"]["Verbose Prompting"]
        return prompt if isinstance(prompt, str) else " ".join(prompt)

    # Synthetic verbose expansion
    return (
        f"I need you to help me with the following task: {task}. "
        f"Please make sure to consider all aspects of this request. "
        f"The task involves {task.lower()} and I need it done correctly. "
        f"Let me explain in more detail what I mean by {task.lower()}. "
        f"Each step should be executed in the proper order with all dependencies satisfied. "
        f"Please confirm you understand before proceeding."
    )


def get_prompt_for_mode(task: str, mode: str) -> str | list[str]:
    """Get the example prompt for a specific task and mode.

    Returns string for single-prompt modes, list for clarification mode.
    """
    example = get_example(task)
    if example and mode in example["prompts"]:
        return example["prompts"][mode]

    # Synthetic fallback
    if mode == "Verbose Prompting":
        return get_verbose_prompt(task)
    elif mode == "Clarification Heavy":
        return [
            f"Can you help with: {task}?",
            "What specifically do you need?",
            f"I need {task.lower()}.",
            "Any particular constraints?",
            "Just make sure it works correctly.",
            "OK, proceeding with the standard approach.",
        ]
    elif mode == "Context-Aware":
        words = task.split()
        return f"{task}. Handle dependencies automatically, validate on completion."
    else:  # Intent-Optimized
        return get_optimized_prompt(task)

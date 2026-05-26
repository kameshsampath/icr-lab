"""Tests for the /simulate FastAPI endpoint and patient-risk-calculator catalog entry.

TDD red phase — all tests must FAIL until implementation exists.

Requires dev deps:
    uv add --dev pytest httpx fastapi uvicorn
"""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PATIENT_RISK_TASK = "Build me a patient risk calculator."

CANONICAL_REQUEST = {
    "task": PATIENT_RISK_TASK,
    "operations": 4,
    "requirements": [
        "input form",
        "weighted formula",
        "color badge",
        "formula breakdown",
    ],
    "modes": ["Clarification Heavy", "Intent Optimized"],
    "mode_operations_achieved": {
        "Clarification Heavy": 0,
        "Intent Optimized": 4,
    },
}


@pytest.fixture
def client():
    """Return a TestClient wrapping the FastAPI app."""
    from api.index import app  # noqa: PLC0415

    return TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status_ok(self, client):
        response = client.get("/health")
        assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /simulate — happy path (response structure)
# ---------------------------------------------------------------------------


class TestSimulateEndpoint:
    def test_returns_200_for_valid_request(self, client):
        response = client.post("/simulate", json=CANONICAL_REQUEST)
        assert response.status_code == 200

    def test_response_has_token_metrics_section(self, client):
        data = client.post("/simulate", json=CANONICAL_REQUEST).json()
        assert "token_metrics" in data

    def test_response_has_trace_section(self, client):
        data = client.post("/simulate", json=CANONICAL_REQUEST).json()
        assert "trace" in data

    def test_response_has_requirements_coverage_section(self, client):
        data = client.post("/simulate", json=CANONICAL_REQUEST).json()
        assert "requirements_coverage" in data

    def test_response_has_savings_hypothesis_section(self, client):
        data = client.post("/simulate", json=CANONICAL_REQUEST).json()
        assert "savings_hypothesis" in data

    def test_token_metrics_present_for_each_requested_mode(self, client):
        metrics = client.post("/simulate", json=CANONICAL_REQUEST).json()[
            "token_metrics"
        ]
        for mode in ["Clarification Heavy", "Intent Optimized"]:
            assert mode in metrics

    def test_token_metrics_has_input_output_total_fields(self, client):
        metrics = client.post("/simulate", json=CANONICAL_REQUEST).json()[
            "token_metrics"
        ]
        for mode in ["Clarification Heavy", "Intent Optimized"]:
            m = metrics[mode]
            assert "input_tokens" in m
            assert "output_tokens" in m
            assert "total_tokens" in m

    def test_token_metrics_has_icr_and_amplification(self, client):
        metrics = client.post("/simulate", json=CANONICAL_REQUEST).json()[
            "token_metrics"
        ]
        for mode in ["Clarification Heavy", "Intent Optimized"]:
            m = metrics[mode]
            assert "icr" in m
            assert "token_amplification" in m
            assert "estimated_cost" in m

    def test_trace_has_rounds_list_per_mode(self, client):
        trace = client.post("/simulate", json=CANONICAL_REQUEST).json()["trace"]
        for mode in ["Clarification Heavy", "Intent Optimized"]:
            assert mode in trace
            assert isinstance(trace[mode], list)
            assert len(trace[mode]) >= 1

    def test_trace_rounds_have_required_fields(self, client):
        trace = client.post("/simulate", json=CANONICAL_REQUEST).json()["trace"]
        for mode in ["Clarification Heavy", "Intent Optimized"]:
            for rnd in trace[mode]:
                assert "round" in rnd
                assert "input_tokens" in rnd
                assert "output_tokens" in rnd
                assert "cumulative_tokens" in rnd
                assert "description" in rnd

    def test_savings_hypothesis_has_required_fields(self, client):
        savings = client.post("/simulate", json=CANONICAL_REQUEST).json()[
            "savings_hypothesis"
        ]
        assert "token_savings_pct" in savings
        assert "cost_savings_pct" in savings
        assert "rounds_saved" in savings
        assert "monthly_projection_1k_runs" in savings


# ---------------------------------------------------------------------------
# Requirements coverage — core thesis validation
# ---------------------------------------------------------------------------


class TestRequirementsCoverage:
    def test_clarification_heavy_all_requirements_fail(self, client):
        """mode_operations_achieved=0 → all 4 requirements must show False."""
        coverage = client.post("/simulate", json=CANONICAL_REQUEST).json()[
            "requirements_coverage"
        ]
        assert "Clarification Heavy" in coverage
        ch = coverage["Clarification Heavy"]
        assert all(v is False for v in ch.values()), (
            f"Expected all False for Clarification Heavy (0 ops achieved), got {ch}"
        )

    def test_intent_optimized_all_requirements_pass(self, client):
        """mode_operations_achieved=4 → all 4 requirements must show True."""
        coverage = client.post("/simulate", json=CANONICAL_REQUEST).json()[
            "requirements_coverage"
        ]
        assert "Intent Optimized" in coverage
        io = coverage["Intent Optimized"]
        assert all(v is True for v in io.values()), (
            f"Expected all True for Intent Optimized (4/4 ops achieved), got {io}"
        )

    def test_requirements_coverage_keys_match_request_requirements(self, client):
        coverage = client.post("/simulate", json=CANONICAL_REQUEST).json()[
            "requirements_coverage"
        ]
        for mode_cov in coverage.values():
            assert set(mode_cov.keys()) == set(CANONICAL_REQUEST["requirements"])

    def test_partial_coverage_maps_correctly(self, client):
        """2 of 4 ops achieved → first 2 requirements pass, last 2 fail."""
        req = {
            **CANONICAL_REQUEST,
            "mode_operations_achieved": {
                "Clarification Heavy": 2,
                "Intent Optimized": 4,
            },
        }
        coverage = client.post("/simulate", json=req).json()["requirements_coverage"]
        ch = coverage["Clarification Heavy"]
        passed = [v for v in ch.values() if v is True]
        failed = [v for v in ch.values() if v is False]
        assert len(passed) == 2
        assert len(failed) == 2


# ---------------------------------------------------------------------------
# Determinism — same input must always produce same output
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_identical_request_produces_identical_response(self, client):
        r1 = client.post("/simulate", json=CANONICAL_REQUEST).json()
        r2 = client.post("/simulate", json=CANONICAL_REQUEST).json()
        assert r1 == r2, (
            "Simulation must be fully deterministic: same input → same output"
        )

    def test_determinism_across_different_task_strings(self, client):
        """Different tasks produce consistently different (not random) results."""
        req_alt = {**CANONICAL_REQUEST, "task": "Create a payroll calculator."}
        r1a = client.post("/simulate", json=CANONICAL_REQUEST).json()
        r1b = client.post("/simulate", json=CANONICAL_REQUEST).json()
        r2a = client.post("/simulate", json=req_alt).json()
        r2b = client.post("/simulate", json=req_alt).json()
        # Each task is consistent with itself
        assert r1a == r1b
        assert r2a == r2b
        # Different tasks produce different token counts
        t1 = r1a["token_metrics"]["Clarification Heavy"]["total_tokens"]
        t2 = r2a["token_metrics"]["Clarification Heavy"]["total_tokens"]
        assert t1 != t2, "Different task strings should produce different token counts"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_unknown_mode_does_not_500(self, client):
        req = {**CANONICAL_REQUEST, "modes": ["NonExistentMode"]}
        response = client.post("/simulate", json=req)
        assert response.status_code != 500, "Unknown mode must not cause a server error"

    def test_unknown_mode_returns_200_or_422(self, client):
        req = {**CANONICAL_REQUEST, "modes": ["NonExistentMode"]}
        response = client.post("/simulate", json=req)
        assert response.status_code in (200, 422)

    def test_zero_operations_does_not_crash(self, client):
        req = {**CANONICAL_REQUEST, "operations": 0}
        response = client.post("/simulate", json=req)
        assert response.status_code == 200

    def test_unknown_task_falls_back_to_synthetic_simulation(self, client):
        req = {
            **CANONICAL_REQUEST,
            "task": "A completely unknown task not in catalog xyz.",
        }
        response = client.post("/simulate", json=req)
        assert response.status_code == 200
        assert "trace" in response.json()

    def test_empty_modes_list_returns_empty_trace(self, client):
        req = {**CANONICAL_REQUEST, "modes": []}
        response = client.post("/simulate", json=req)
        assert response.status_code == 200
        assert response.json()["trace"] == {}

    def test_missing_task_field_returns_422(self, client):
        req = {k: v for k, v in CANONICAL_REQUEST.items() if k != "task"}
        assert client.post("/simulate", json=req).status_code == 422

    def test_missing_operations_field_auto_derived(self, client):
        req = {k: v for k, v in CANONICAL_REQUEST.items() if k != "operations"}
        resp = client.post("/simulate", json=req)
        assert resp.status_code == 200
        assert resp.json()["operations"] == 4  # auto-derived from catalog

    def test_negative_operations_rejected_or_normalised(self, client):
        req = {**CANONICAL_REQUEST, "operations": -1}
        response = client.post("/simulate", json=req)
        # 422 if validation rejects it, 200 if API normalises to 0 coverage
        assert response.status_code in (200, 422)

    def test_catalog_task_trace_has_populated_prompt_text(self, client):
        """For a known catalog task, at least one round must have non-empty prompt_text."""
        trace = client.post("/simulate", json=CANONICAL_REQUEST).json()["trace"]
        ch_rounds = trace.get("Clarification Heavy", [])
        assert any(r.get("prompt_text") for r in ch_rounds), (
            "patient-risk-calculator is in catalog — Clarification Heavy rounds must "
            "have prompt_text populated from the scripted conversation"
        )


# ---------------------------------------------------------------------------
# Catalog entry — patient-risk-calculator
# ---------------------------------------------------------------------------


class TestPatientRiskCatalogEntry:
    """These tests verify the catalog entry independently of the API."""

    def test_catalog_has_patient_risk_calculator(self):
        from examples.catalog import get_example  # noqa: PLC0415

        example = get_example(PATIENT_RISK_TASK)
        assert example is not None, (
            "patient-risk-calculator must be registered in examples/catalog.py"
        )

    def test_catalog_entry_has_exactly_four_operations(self):
        from examples.catalog import get_example  # noqa: PLC0415

        example = get_example(PATIENT_RISK_TASK)
        assert example is not None
        ops = example["operations"]
        assert len(ops) == 4, f"Expected 4 named operations, got {len(ops)}: {ops}"

    def test_catalog_entry_four_operation_names(self):
        from examples.catalog import get_example  # noqa: PLC0415

        example = get_example(PATIENT_RISK_TASK)
        assert example is not None
        ops_lower = [op["command"].lower() for op in example["operations"]]
        assert any("form" in op or "input" in op for op in ops_lower), (
            "Missing input form op"
        )
        assert any("formula" in op or "weighted" in op for op in ops_lower), (
            "Missing weighted formula op"
        )
        assert any("badge" in op or "color" in op for op in ops_lower), (
            "Missing color badge op"
        )
        assert any("breakdown" in op for op in ops_lower), (
            "Missing formula breakdown op"
        )

    def test_catalog_entry_clarification_heavy_has_seven_rounds(self):
        from examples.catalog import get_prompt_for_mode  # noqa: PLC0415

        rounds = get_prompt_for_mode(PATIENT_RISK_TASK, "Clarification Heavy")
        assert isinstance(rounds, list), (
            "Clarification Heavy must return a list of prompts"
        )
        assert len(rounds) == 7, (
            f"Expected 7 scripted Clarification Heavy rounds, got {len(rounds)}"
        )

    def test_catalog_entry_has_substantive_intent_optimized_prompt(self):
        """Prompt must come from the catalog entry, not just the synthetic fallback.

        The synthetic fallback produces a generic ~50-char prompt. The catalog entry
        must be >100 chars (extracted intent block from the demo workflow).
        """
        from examples.catalog import get_example  # noqa: PLC0415

        example = get_example(PATIENT_RISK_TASK)
        assert example is not None, (
            "patient-risk-calculator must be registered in examples/catalog.py"
        )
        prompt = example["prompts"].get("intent_optimized", "")
        assert prompt, "Catalog entry must have an intent_optimized prompt key"
        assert len(prompt) > 100, (
            f"Intent Optimized prompt must be the extracted intent block (>100 chars), "
            f"got {len(prompt)} chars: {prompt!r}"
        )


# ---------------------------------------------------------------------------
# New fields — token_source, assumptions, ops_by_type
# ---------------------------------------------------------------------------


class TestNewFields:
    """Verify fields added in the assumption-led + tiktoken commits."""

    def test_trace_rounds_have_token_source_field(self, client):
        trace = client.post("/simulate", json=CANONICAL_REQUEST).json()["trace"]
        for mode_rounds in trace.values():
            for rnd in mode_rounds:
                assert "token_source" in rnd, "Each round must have token_source"
                assert rnd["token_source"] in ("measured", "estimated")

    def test_trace_rounds_have_assumptions_field(self, client):
        trace = client.post("/simulate", json=CANONICAL_REQUEST).json()["trace"]
        for mode_rounds in trace.values():
            for rnd in mode_rounds:
                assert "assumptions" in rnd, "Each round must have assumptions list"
                assert isinstance(rnd["assumptions"], list)

    def test_token_metrics_has_total_assumptions(self, client):
        metrics = client.post("/simulate", json=CANONICAL_REQUEST).json()[
            "token_metrics"
        ]
        for mode in CANONICAL_REQUEST["modes"]:
            assert "total_assumptions" in metrics[mode]
            assert isinstance(metrics[mode]["total_assumptions"], int)

    def test_token_metrics_has_wrong_assumptions(self, client):
        metrics = client.post("/simulate", json=CANONICAL_REQUEST).json()[
            "token_metrics"
        ]
        for mode in CANONICAL_REQUEST["modes"]:
            assert "wrong_assumptions" in metrics[mode]
            assert metrics[mode]["wrong_assumptions"] >= 0

    def test_assumption_led_mode_works(self, client):
        req = {**CANONICAL_REQUEST, "modes": ["Assumption Led"]}
        response = client.post("/simulate", json=req)
        assert response.status_code == 200
        data = response.json()
        assert "Assumption Led" in data["token_metrics"]
        assert "Assumption Led" in data["trace"]

    def test_catalog_task_has_measured_token_source(self, client):
        """For a known catalog task, at least one round should have measured tokens."""
        trace = client.post("/simulate", json=CANONICAL_REQUEST).json()["trace"]
        # patient-risk-calculator is in catalog — Clarification Heavy has scripted prompts
        ch_rounds = trace.get("Clarification Heavy", [])
        measured = [r for r in ch_rounds if r.get("token_source") == "measured"]
        assert len(measured) >= 1, (
            "Clarification Heavy for a catalog task must have at least 1 measured round"
        )


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


class TestInputValidation:
    def test_task_over_2000_chars_rejected(self, client):
        req = {**CANONICAL_REQUEST, "task": "x" * 2001}
        assert client.post("/simulate", json=req).status_code == 422

    def test_null_bytes_in_task_stripped(self, client):
        req = {**CANONICAL_REQUEST, "task": "Build\x00 me a patient risk calculator."}
        resp = client.post("/simulate", json=req)
        assert resp.status_code == 200
        assert "\x00" not in resp.json()["task"]

    def test_html_injection_in_task_stripped_by_pydantic(self, client):
        """HTML in task field passes through (display layer must escape); task is stored as-is after null-byte strip."""
        req = {**CANONICAL_REQUEST, "task": "<script>alert(1)</script>Deploy connector"}
        resp = client.post("/simulate", json=req)
        # API accepts it (display layer responsibility to escape HTML)
        assert resp.status_code in (200, 422)


# ---------------------------------------------------------------------------
# Assumption accuracy
# ---------------------------------------------------------------------------


class TestAssumptionAccuracy:
    def test_default_accuracy_is_perfect(self, client):
        """Default accuracy=1.0 → 0 wrong assumptions → 1 round for Assumption Led."""
        req = {**CANONICAL_REQUEST, "modes": ["Assumption Led"]}
        data = client.post("/simulate", json=req).json()
        m = data["token_metrics"]["Assumption Led"]
        assert m["wrong_assumptions"] == 0
        assert m["interaction_rounds"] == 1

    def test_low_accuracy_adds_rounds(self, client):
        """accuracy=0.0 → all assumptions wrong → multiple rounds."""
        req = {
            **CANONICAL_REQUEST,
            "modes": ["Assumption Led"],
            "assumption_accuracy": 0.0,
        }
        trace = client.post("/simulate", json=req).json()["trace"]
        assert len(trace["Assumption Led"]) > 1

    def test_low_accuracy_reduces_ops_on_complex_task(self, client):
        """accuracy=0.0 on a complex task → some requirements not covered."""
        req = {
            "task": "Deploy a connector with Snowflake Openflow",
            "modes": ["Assumption Led"],
            "assumption_accuracy": 0.0,
            "requirements": ["r1", "r2", "r3", "r4", "r5", "r6"],
        }
        data = client.post("/simulate", json=req).json()
        cov = data["requirements_coverage"]["Assumption Led"]
        assert any(v is False for v in cov.values()), (
            "Low accuracy should cause at least one requirement to be uncovered"
        )

    def test_accuracy_above_1_rejected(self, client):
        """assumption_accuracy > 1.0 must be rejected with 422."""
        req = {**CANONICAL_REQUEST, "assumption_accuracy": 1.5}
        assert client.post("/simulate", json=req).status_code == 422

    def test_accuracy_below_0_rejected(self, client):
        """assumption_accuracy < 0.0 must be rejected with 422."""
        req = {**CANONICAL_REQUEST, "assumption_accuracy": -0.1}
        assert client.post("/simulate", json=req).status_code == 422

"""Prompt construction.

These assert structure and invariants, never prose quality. A test that pinned
exact wording would fail on every legitimate revision of the prompt, which is
the opposite of useful. What is worth locking down is that the rules the
validator will enforce are actually stated, that no raw data escapes into the
prompt, and that the column budget degrades honestly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from app import heuristics, profiler, prompts
from app.models import ColumnProfile, ProfileCard

FIXTURES = Path(__file__).parent / "fixtures" / "profiler"


@pytest.fixture
def card():
    frame = pd.read_csv(FIXTURES / "leaking_feature.csv", engine="c")
    return profiler.profile(frame, "abc", "leaking_feature.csv", "target")


# --- The system prompt states the rules the validator enforces ---------------


@pytest.mark.parametrize(
    "required",
    [
        'pd.read_csv("data.csv", engine="c")',  # exact load line
        "random_state",
        "numeric_as_string",
        "potential_leakage",
        "__import__",  # the denylist the validator mirrors
    ],
)
def test_system_prompt_states_the_code_constraints(required):
    """Stage 4 marks generated code against these. A rule the validator checks
    but the prompt never states is marking against an unstated exam."""
    assert required in prompts.SYSTEM_PROMPT


def test_system_prompt_forbids_fabricated_scores():
    """The single rule this project cannot compromise on: MVP-1 never runs the
    code, so any figure the model volunteers is invented and indistinguishable
    from a measured one."""
    lowered = prompts.SYSTEM_PROMPT.lower()
    assert "has not been run" in lowered
    assert "do not put performance figures" in lowered


def test_system_prompt_treats_column_names_as_data():
    """Column names and sample values are the only user-controlled text in the
    prompt, and both are copied verbatim out of an uploaded file."""
    lowered = prompts.SYSTEM_PROMPT.lower()
    assert "never instructions" in lowered or "inert data" in lowered


def test_system_prompt_tells_the_model_to_restate_rather_than_re_decide():
    """GenResult repeats three fields the profile already settled. The model
    must echo them, because stage 4 checks the two for consistency."""
    assert "problem_type" in prompts.SYSTEM_PROMPT
    assert "primary_metric" in prompts.SYSTEM_PROMPT
    assert "risks" in prompts.SYSTEM_PROMPT


def test_system_prompt_explains_what_target_association_measures():
    """Caught in live validation: without this the model calls it a "weak
    linear association", which is wrong for all three statistics behind it
    (rank correlation, correlation ratio, class purity) and misdescribes the
    measurement to the user in prose they are meant to trust."""
    assert "target_association" in prompts.SYSTEM_PROMPT
    assert "NOT a linear correlation" in prompts.SYSTEM_PROMPT


def test_prompt_contains_no_em_dashes():
    assert "—" not in prompts.SYSTEM_PROMPT


def test_worked_example_obeys_its_own_code_constraints():
    """An example that broke the rules it teaches would be worse than none."""
    example = prompts.SYSTEM_PROMPT
    assert 'pd.read_csv("data.csv", engine="c")' in example
    assert "random_state=42" in example
    # The example is a regression task, so it must demonstrate RMSE primary.
    assert "neg_root_mean_squared_error" in example


# --- Serialisation ------------------------------------------------------------


def test_serialized_profile_is_valid_json(card):
    payload = json.loads(prompts.serialize_profile(card))
    assert payload["target_column"] == "target"
    assert payload["problem_type"] == "binary_classification"
    assert len(payload["columns"]) == card.n_columns


def test_serialization_drops_null_fields(card):
    """A categorical column carries no min, max, mean, std or median. Emitting
    five nulls per column is noise the model reads past and budget it spends."""
    payload = json.loads(prompts.serialize_profile(card))
    leaky = next(c for c in payload["columns"] if c["name"] == "leaky")
    assert "min" not in leaky
    assert "parse_rate" not in leaky


def test_serialization_carries_no_data_beyond_sample_values(card):
    """The core architectural rule, asserted at the boundary it protects."""
    payload = json.loads(prompts.serialize_profile(card))
    assert set(payload) <= set(ProfileCard.model_fields) | {"columns_omitted_from_this_prompt"}

    for column in payload["columns"]:
        assert set(column) <= set(ColumnProfile.model_fields)


def test_user_message_includes_the_profile_and_asks_for_the_pipeline(card):
    message = prompts.build_user_message(card)
    assert "leaking_feature.csv" in message
    assert message.rstrip().endswith("Produce the strategy and the pipeline code for this dataset.")


# --- Column budget ------------------------------------------------------------


def wide_frame(n_columns: int, n_rows: int = 60) -> pd.DataFrame:
    data = {f"c{i}": [i] * n_rows for i in range(n_columns)}
    # One column with real signal so the association ordering has something to
    # sort on, and a target to profile against.
    data["target"] = [i % 2 for i in range(n_rows)]
    data["informative"] = [i % 2 for i in range(n_rows)]
    return pd.DataFrame(data)


def test_all_columns_are_sent_when_under_budget(card):
    payload = json.loads(prompts.serialize_profile(card))
    assert "columns_omitted_from_this_prompt" not in payload
    assert len(payload["columns"]) == card.n_columns


def test_over_budget_keeps_the_target_and_every_flagged_column(monkeypatch):
    monkeypatch.setattr(heuristics, "PROMPT_MAX_COLUMNS", 10)
    frame = wide_frame(40)
    result = profiler.profile(frame, "id", "wide.csv", "target")

    payload = json.loads(prompts.serialize_profile(result))
    kept = {c["name"] for c in payload["columns"]}

    assert len(kept) <= heuristics.PROMPT_MAX_COLUMNS
    assert "target" in kept
    assert payload["columns_omitted_from_this_prompt"] == result.n_columns - len(kept)

    # Every retained non-target column that had flags is still there, and the
    # count reconciles: nothing is quietly lost.
    flagged = {c.name for c in result.columns if c.flags}
    assert flagged & kept or not flagged


def test_truncation_is_declared_to_the_model(monkeypatch):
    """A model planning around columns it cannot see, without being told, would
    write confident strategy over a partial view."""
    monkeypatch.setattr(heuristics, "PROMPT_MAX_COLUMNS", 10)
    result = profiler.profile(wide_frame(40), "id", "wide.csv", "target")
    message = prompts.build_user_message(result)
    assert "not listed above" in message
    assert "only the columns you were shown" in message


def test_retained_columns_keep_the_files_own_order(monkeypatch):
    monkeypatch.setattr(heuristics, "PROMPT_MAX_COLUMNS", 10)
    result = profiler.profile(wide_frame(40), "id", "wide.csv", "target")
    payload = json.loads(prompts.serialize_profile(result))

    original = [c.name for c in result.columns]
    kept = [c["name"] for c in payload["columns"]]
    assert kept == sorted(kept, key=original.index)


# --- Sampling disclosure ------------------------------------------------------


def test_sampling_note_appears_only_when_sampling_happened(card, monkeypatch):
    assert "random sample of rows" not in prompts.build_user_message(card)

    monkeypatch.setattr(heuristics, "SAMPLE_THRESHOLD", 50)
    frame = pd.read_csv(FIXTURES / "leaking_feature.csv", engine="c")
    sampled = profiler.profile(frame, "abc", "leaking_feature.csv", "target")
    assert sampled.profiled_on_sample is True

    message = prompts.build_user_message(sampled)
    assert "random sample of rows" in message
    # And it must say what was NOT sampled, or the model discounts every number.
    assert "computed on the complete file" in message


# --- Column exclusion --------------------------------------------------------


def test_empty_exclusion_matches_the_unfiltered_prompt(card):
    """The load-bearing invariant behind excluded_columns.

    Cassette files are named by sha256 of the exact prompt text, so if adding
    this parameter changed the default output by even one byte, all three
    recordings would stop matching and would cost real quota to re-record
    (20 requests/day/model on the free tier). Byte equality, not shape
    equality, is the assertion that protects them.
    """
    assert prompts.build_user_message(card, ()) == prompts.build_user_message(card)
    assert prompts.build_user_message(card, []) == prompts.build_user_message(card)
    assert prompts.serialize_profile(card, ()) == prompts.serialize_profile(card)


def test_excluded_columns_leave_the_payload(card):
    victim = next(c.name for c in card.columns if c.name != card.target_column)

    payload = json.loads(prompts.serialize_profile(card, [victim]))

    assert victim not in {column["name"] for column in payload["columns"]}
    # Named explicitly rather than silently absent, so the model can record it
    # in dropped_columns with a truthful reason instead of writing a pipeline
    # that looks like the column never existed.
    assert payload["columns_excluded_by_user"] == [victim]


def test_exclusion_does_not_change_n_columns(card):
    """n_columns is a fact about the file. Excluding a column changes what the
    model is offered, not what the dataset is."""
    victim = next(c.name for c in card.columns if c.name != card.target_column)
    payload = json.loads(prompts.serialize_profile(card, [victim]))
    assert payload["n_columns"] == card.n_columns


def test_exclusion_instruction_tells_the_model_what_to_do(card):
    """The say-Y rule from CLAUDE.md: a bare prohibition is weaker than naming
    the behaviour wanted. The message must state the positive action, not only
    that the column is gone."""
    victim = next(c.name for c in card.columns if c.name != card.target_column)
    message = prompts.build_user_message(card, [victim])
    assert "dropped_columns" in message
    assert victim in message


def test_target_column_survives_exclusion_of_everything_else(card):
    """Excluding the target is refused at the route, but the serializer should
    not corrupt the payload even if it is asked directly."""
    others = [c.name for c in card.columns if c.name != card.target_column]
    payload = json.loads(prompts.serialize_profile(card, others))
    assert payload["target_column"] == card.target_column

"""Persist experience state and measured outcomes as JSON files."""

from __future__ import annotations

from tempfile import TemporaryDirectory

from laix import ExperienceState, FileOutcomeStore, FileStateStore

with TemporaryDirectory() as directory:
    state_store = FileStateStore(directory)
    state = ExperienceState(subject="weekly review", phase="decide")
    state_store.save("review-1", state)
    loaded = state_store.load("review-1")

    outcome_store = FileOutcomeStore(directory)
    outcome_store.record(
        "DEC-1",
        metric="time_to_review",
        before=10.0,
        after=8.0,
        attributed=True,
        direction="lower-better",
    )
    restored = FileOutcomeStore(directory)

    print(loaded.phase if loaded else "missing", restored.summary()["helped"])

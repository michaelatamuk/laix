"""Keep an experience snapshot between turns without owning a database.

The result is:

    decide True

- decide: the phase that was saved and loaded again.
- True: deleting the key removed the snapshot.
"""

from laix import ExperienceState, InMemoryStateStore

store = InMemoryStateStore()
state = ExperienceState(subject="weekly review", phase="decide")

store.save("review-1", state)
loaded = store.load("review-1")
store.delete("review-1")

print(loaded.phase, store.load("review-1") is None)

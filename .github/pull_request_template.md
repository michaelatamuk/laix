## Summary

What changed, and why?

## Checks

- [ ] `python -m pytest -q`
- [ ] `python -m ruff check .`
- [ ] `npm run build && npm run typecheck && npm run typecheck:declarations && npm run check:consumer`
- [ ] `npm test`
- [ ] `python scripts/ci/check_docs_links.py`

## Compatibility

- [ ] No public API change
- [ ] Additive API change
- [ ] Breaking change with a migration note
- [ ] Schema, reason-code or vector change

## Notes

Anything the reviewer should know: rollout, rollback, limits or follow-up work.

## What does this change, and why?

<!-- What problem does this solve? Link an issue if there is one. -->

## How was this tested?

<!-- pytest output, a screenshot of the frontend, whatever demonstrates it works. -->

## Checklist

- [ ] Backend: `ruff format . && ruff check .` and `pytest` pass, from `backend/`
- [ ] Frontend: `npm run lint` and `npm run build` pass, from `frontend/` (if touched)
- [ ] If this changes a color-space conversion or color-difference formula, it includes a test against an independently sourced reference, not just the implementation's own derivation (see CONTRIBUTING.md)
- [ ] This PR does one thing; unrelated cleanup is in a separate PR

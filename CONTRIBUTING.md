# Contributing to Hueclid

Thanks for taking a look. This is an early-stage project, both a tool and a research effort around accessible color palette generation, so the shape of "how to contribute" is a little different from a mature codebase: the architecture is still settling, and some pieces described in the README (the clustering engine, the constraint solver, the evaluation pipeline) don't exist yet. That's not a problem, it's just useful context before you dive in.

## `main` is what's actually running

Hueclid is hosted at https://hueclid.cinexg.com, and that site runs off `main`. Nothing gets pushed to `main` directly, not by outside contributors, who wouldn't have push access to do that anyway, and not by the maintainer either. Every change, however small, goes through a branch and a pull request. This is enforced on GitHub's side: a pull request and a green CI run on both `backend` and `frontend` are required before anything can merge.

In practice this changes nothing about how you'd already be contributing, fork or branch, then open a pull request, is the normal flow either way. It just means there's no direct-push shortcut for anyone, including whoever's merging it.

## Before you start on something big

If you're fixing a bug, improving a test, or cleaning up something small, just open a pull request. For anything larger, a new feature, a new color-space implementation, a change to the API shape, please open an issue first to talk it through. The roadmap is still being figured out in places, and it's much better to align before you put real time into something than after.

## Getting the project running

**Backend** (Python, FastAPI) from `backend/`:

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

**Frontend** (Next.js, TypeScript) from `frontend/`:

```
npm install
npm run dev
```

That's the whole thing. No accounts, no external services, no dataset downloads. Everything runs and gets tested on localhost.

## Background reading

If you want to understand the color math and the reasoning behind the approach before touching the code, `math-explained/` has the deeper write-up on the math, and the [wiki](https://github.com/gauravxsuvo/Hueclid/wiki) covers the idea, the theory, and how the current architecture actually works end to end. Worth reading before proposing changes to anything under `backend/app/color/`.

## The one rule that actually matters: verify color math against a reference

This is the single most important convention in the codebase. Color-science formulas (CIEDE2000, Oklab, APCA, gamut mapping, any new color-space conversion) look plausible even when they're subtly wrong, a transposed digit in a matrix constant produces numbers that are close enough to right that nothing catches it by inspection. It will pass code review. It will not pass reality.

So: any change to a color-space conversion or a color-difference formula needs a test that checks the implementation against an independently sourced reference, not just against your own derivation of the same formula. `backend/tests/test_color_conformance.py` is the model to follow, it checks the CIEDE2000 implementation against all 34 published test pairs from Sharma, Wu & Dalal (2005), pulled directly from a working reference implementation rather than retyped by hand. If you're adding, say, Oklab support, the equivalent would be checking against Björn Ottosson's published reference values.

PRs touching `backend/app/color/` without a conformance test attached will get asked for one before merge.

## Code style

**Python**: formatted and linted with [ruff](https://docs.astral.sh/ruff/). Run `ruff format .` and `ruff check .` from `backend/` before opening a PR. CI runs both.

**TypeScript**: standard Next.js/ESLint config, already set up. Run `npm run lint` from `frontend/`.

Neither is strict about style nitpicks beyond what the linters catch, if the linter is happy, the formatting is fine.

## Tests

Backend changes need tests. `pytest` from `backend/` should pass, and if you're touching the API, add a test in `backend/tests/test_api_extract.py` or a new file following the same pattern. Frontend changes should at minimum keep `npm run build` and `npm run lint` passing; component tests aren't set up yet, so use your judgment on whether a change needs one.

## Commit messages and pull requests

Write commit messages that explain why a change was made, not just what changed, the diff already shows what changed. Keep PRs focused on one thing; a PR that fixes a bug and also reformats an unrelated file is harder to review and harder to revert if something goes wrong.

Every PR runs through CI (tests, lint, type-check, build) automatically. Please make sure it's green before asking for review.

## License

Hueclid is MIT licensed. By contributing, you agree your contributions are licensed under the same terms. See `LICENSE`.

## Code of conduct

This project follows the guidelines in `CODE_OF_CONDUCT.md`. Please read it before participating.

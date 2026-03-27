# Contributing

Thanks for your interest in Meal.OS.

## Development Setup

1. Install backend dependencies from [README.md](/Users/aravind/KruxAI/Meal.OS/README.md).
2. Install frontend dependencies from [README.md](/Users/aravind/KruxAI/Meal.OS/README.md).
3. Copy the root `.env.example` into the app-specific env files you need:
   - `backend/.env`
   - `frontend/.env.local`

## Working Style

- Keep changes focused and reviewable.
- Prefer test-first updates for behavior changes.
- Preserve the India-first household meal-planning context of the product.
- Avoid re-introducing private household-specific narrative or real personal data.

## Verification

Before opening a PR:

```bash
cd frontend && npx vitest run
cd backend && pytest -v
```

If you touch public-facing copy, also check:

- branding still reads `Meal.OS`
- docs are consistent with the current product
- no private household details appear in user-facing files

# Contributing to visa-verifier

Thanks for taking the time. This is a small project but accuracy of the generated dataset matters, so a few conventions below.

## Reporting a data error

The fastest way: open a GitHub issue titled `Wrong entry: <passport> → <destination>` with:

1. The entry as it currently is in `output/verified-visas.json` (copy-paste the JSON object)
2. The URL of the official government page that contradicts it
3. One-line summary of what's wrong

Don't open an issue for an entry that's just *missing* — those get filled in automatically as the verifier expands. Only open issues for entries that are present but wrong.

## Proposing a new trusted-domain pattern

If the verifier is downgrading legitimate gov sources to `low` confidence, the fix is usually to add the domain to `TRUSTED_PATTERNS` in `verifier.py`.

Process:

1. Find 2+ different verified entries (by eye — check the model said it was high-confidence but the domain gate forced it to `low`) that cite the same domain family.
2. Confirm the domain really is a government-run source (not a contractor dressed up as one).
3. Open a PR that adds the pattern to `TRUSTED_PATTERNS` with a comment explaining which country and which ministry/department it belongs to.
4. Run `python reclassify.py` locally — the PR should include the updated `output/verified-visas.json` showing the promoted confidence levels.

## Adding passports or destinations to cover

Edit `config.json` — `passports[]` and `destinations[]` are plain JSON arrays. Add an entry, open a PR. Whoever's running the verifier will pick up the new pair on the next scheduled run.

## Code changes

PRs welcome for:
- Better rate-limit handling when `--parallel > 4`
- Better prompt engineering (cheaper calls, fewer searches)
- Additional output formats (Parquet, SQLite, etc.)
- Alternative LLM backends (OpenAI, Gemini — would need the subprocess shape adapted)

Please keep PRs small and single-purpose. Run `python agent.py --dry-run` locally to confirm nothing explodes before submitting.

## Non-goals

Things this project deliberately won't do:

- **Accept commercial-aggregator URLs** (iVisa, PassportIndex.com, visaguide.world) as sources, even if the model wants to. We only trust gov domains.
- **Claim 100% accuracy**. The README and on-site copy clearly say "always verify with the embassy before booking." We calibrate honestly.
- **Run a paid API tier**. If you want something faster/more-accurate, use Sherpa or IATA Timatic — they're commercial for a reason.
- **Translate notes into non-English**. Source pages are in many languages; `notes` is deliberately English-only for consistency. Translation belongs in a downstream tool.

## Code of conduct

Be kind. The visa/immigration space touches people at vulnerable moments — if a change benefits 99% of users but breaks a critical edge case for a minority, we prioritise the minority.

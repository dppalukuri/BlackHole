Visa Matrix 2026 — Government-Sourced Visa Requirements Database
=================================================================

Thank you for your purchase.

What's in this bundle
---------------------
  verified-matrix.csv    Every passport -> destination pair we've verified
                         against an official government source. The key column
                         for trust is `source_url` — it links directly to the
                         embassy/MFA/e-visa page we used.

  residence-permits.csv  Hand-curated exemptions for holders of UAE Residence,
                         US Green Card, Schengen Residence, UK BRP, Canadian
                         PR, valid US B1/B2 visa, and valid Schengen visa.
                         Each row links to its source.

  bulk-matrix.csv        Full 199 x 199 visa matrix from the community-maintained
                         Passport Index Dataset. Ships as a reference baseline
                         for the edge cases we haven't re-verified yet. Not
                         individually sourced.

  report.pdf             Methodology overview, confidence tiers, license terms.
                         Print-friendly.

  VERSION                ISO date of this snapshot + row counts.


Understanding the confidence column
-----------------------------------
  high    Source URL is on a core government domain (.gov, .gov.<cc>,
          travel.state.gov, mofa.*, embassy subdomains). Use directly.

  medium  Source URL is a trusted country-specific portal (canada.ca,
          u.ae, diplo.de, admin.ch, vistoperitalia.it, etc.). Use
          directly; the host is authoritative within its jurisdiction.

  low     Source URL is an aggregator or reference-style site. Kept for
          transparency but flagged — please verify independently before
          acting on a `low` entry.


Understanding the validator_agreed column
-----------------------------------------
We run each entry through TWO models — Claude Haiku does the initial
extraction, then Claude Sonnet re-verifies. This column reports whether
the two models converged:

    yes           Both models returned the same status for this pair.
    no            Disagreement flagged. Worth independent verification.
    (empty)       Sonnet re-verification timed out or hit a rate limit
                  for this specific pair. Original Haiku entry stands.


Important caveats
-----------------
- Visa rules change WITHOUT NOTICE. This is a point-in-time snapshot.
- Always re-verify with the destination embassy before booking travel or
  advising a client.
- Work, student, and transit visa rules differ from tourist visas. This
  dataset covers tourist / short-stay only.
- Some countries extend exemptions only to certain nationalities even
  among residence-permit holders. We note these in the `notes` column
  where applicable.


License
-------
- Personal use, commercial research, internal business use: permitted.
- Client deliverables citing the dataset: permitted with attribution
  ("VisaPathway / TechTools365").
- Redistribution of the raw CSVs as a competing dataset product: NOT
  permitted.


Updates
-------
This is version 2026.X.X — see VERSION file for the exact snapshot date.

Free updates for 12 months from purchase. When a new snapshot is
published, download the latest zip from your Gumroad library.


Support
-------
Spot an error? Reply to your purchase receipt email.

Open-source pipeline & issue tracker:
  https://github.com/dppalukuri/BlackHole/tree/main/autonomous-agents/visa-verifier

=================================================================

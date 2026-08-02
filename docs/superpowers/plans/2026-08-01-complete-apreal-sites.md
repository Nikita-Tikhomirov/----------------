# Complete AP-Real Site Work

## Goal

Close the client request across every included production site. A site is complete only when the current live implementation passes clean-URL functional checks, both real form deliveries, and fresh desktop/mobile visual comparison against the latest requirement.

## Guardrails

- Do not send, draft, reply to, or forward client email.
- Preserve the five explicit form exclusions.
- Back up and verify live state before every publication batch.
- Use clearly marked technical test submissions.
- Do not treat HTTP success, UI success text, or an old client acceptance as proof of mail delivery.
- Do not close a shared implementation until every domain in its family passes.

## Execution

1. Turn the acceptance script into a clean-URL blocking gate: TLS errors, page errors, critical console errors, broken resources, field mismatches, overlap, and failed ordinary clicks fail the domain.
2. Take a fresh server snapshot and compare live hashes with the current generated candidates for the 23 standard, 5 custom `mail.php`, and 2 CF7 sites.
3. Reproduce each failure and identify whether its source is the shared form layer, site integration, cache, mail route, or unrelated page JavaScript.
4. Add a failing regression test for each confirmed root cause, make the smallest family-aware correction, publish atomically, read back hashes, and flush relevant caches.
5. Submit both forms with unique `APREAL-QA-20260801-*` markers on all 30 included domains. Confirm the corresponding messages in the expected mailbox or forwarding route and verify From, Reply-To, subject, and body.
6. Run fresh desktop and mobile visual acceptance on clean URLs for all 30 domains, review the screenshots, and rerun after any correction.
7. Run targeted and full tests, record only current evidence in the internal task state, commit the scoped changes, and publish the repository.

## Completion Gate

No included domain may be reported complete unless all current evidence is present. External DNS or mailbox ownership blockers remain explicit and cannot be converted into success.

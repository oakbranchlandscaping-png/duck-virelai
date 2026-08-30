"""RETIRED — WO-SOV03-CLEANUP §2a (June 6, 2026).

The legacy Tier-3 CLICK tool was unreachable after WO-FM11-FIX removed the
selector's tier3-CLICK dispatch (WO-SOV03-AUDIT §2 A-2: INERT-LATENT — a dead
module that still contained live `rng.randint` emitters if ever re-wired).
Retired in place per the audit's COMPLETE-NOW set; physical file removal rides
the SP8 wave (the build sandbox cannot unlink files).

Captain-owned CLICK dispatch lives in captain.py's DISPATCH_TABLE
(FIRST_TOUCH via tier4_click.emit_click_at_region; CYCLE via the cycle probe).
The context field it once used (`tier3_click_skipped_targets`) remains on
VirelaiContext (persistence-tier bookkeeping; removal is a context-schema
change out of this WO's scope).
"""

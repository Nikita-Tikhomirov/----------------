from datetime import datetime, timedelta, timezone

from tools.client_cycle_lease import acquire_lease, release_lease, renew_lease


NOW = datetime(2026, 7, 29, 8, 0, tzinfo=timezone.utc)


def test_active_lease_prevents_overlapping_cycle():
    state, acquired, recovered = acquire_lease({}, "run-1", NOW, ttl_minutes=90)
    assert acquired is True
    assert recovered is False

    unchanged, acquired, recovered = acquire_lease(
        state,
        "run-2",
        NOW + timedelta(minutes=30),
        ttl_minutes=90,
    )

    assert acquired is False
    assert recovered is False
    assert unchanged == state


def test_expired_lease_is_recovered_automatically():
    state, _, _ = acquire_lease({}, "run-1", NOW, ttl_minutes=90)

    recovered_state, acquired, recovered = acquire_lease(
        state,
        "run-2",
        NOW + timedelta(minutes=91),
        ttl_minutes=90,
    )

    assert acquired is True
    assert recovered is True
    assert recovered_state["run_id"] == "run-2"


def test_only_owner_can_renew_or_release_lease():
    state, _, _ = acquire_lease({}, "run-1", NOW, ttl_minutes=90)

    renewed, ok = renew_lease(
        state,
        "run-1",
        NOW + timedelta(minutes=30),
        ttl_minutes=90,
    )
    assert ok is True
    assert renewed["expires_at"] != state["expires_at"]

    unchanged, ok = release_lease(renewed, "run-2")
    assert ok is False
    assert unchanged == renewed

    released, ok = release_lease(renewed, "run-1")
    assert ok is True
    assert released == {}

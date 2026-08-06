#!/usr/bin/env python3
"""Regression tests for the rating port — every branch of the Supervisor
algorithm, with expectations computed by hand from the cited source
(supervisor/apps/utils.py @ 64961ef, lines 19-86)."""

from rating import rating_security


def r(config, apparmor_profile=False):
    return rating_security(config, apparmor_profile)[0]


def test_baseline_is_5():
    assert r({}) == 5


def test_apparmor():
    assert r({"apparmor": False}) == 4
    assert r({}, apparmor_profile=True) == 6


def test_ingress_beats_auth_api():
    assert r({"ingress": True}) == 7
    assert r({"auth_api": True}) == 6
    assert r({"ingress": True, "auth_api": True}) == 7


def test_signed():
    assert r({"codenotary": "signer@example.com"}) == 6


def test_privileged_counts_once():
    assert r({"privileged": ["SYS_ADMIN"]}) == 4
    assert r({"privileged": ["SYS_ADMIN", "NET_ADMIN", "SYS_RAWIO"]}) == 4
    assert r({"privileged": ["SYS_TIME"]}) == 5  # not in the risky set
    assert r({"kernel_modules": True}) == 4
    assert r({"kernel_modules": True, "privileged": ["SYS_ADMIN"]}) == 4


def test_hassio_role():
    assert r({"hassio_role": "manager"}) == 4
    assert r({"hassio_role": "admin"}) == 3
    assert r({"hassio_role": "default"}) == 5


def test_host_namespaces():
    assert r({"host_network": True}) == 4
    assert r({"host_pid": True}) == 3
    assert r({"host_uts": True}) == 5  # UTS alone is neutral
    assert r({"host_uts": True, "privileged": ["SYS_ADMIN"]}) == 3  # -1 priv, -1 uts


def test_docker_or_full_access_floor_to_1():
    assert r({"docker_api": True, "ingress": True, "codenotary": "x"}) == 1
    assert r({"full_access": True, "ingress": True}) == 1


def test_clamped_to_1_and_8():
    worst = {
        "apparmor": False,
        "privileged": ["SYS_ADMIN"],
        "hassio_role": "admin",
        "host_network": True,
        "host_pid": True,
        "host_uts": True,
    }
    assert r(worst) == 1  # 5-1-1-2-1-2-1 = -3, clamped
    best = {"ingress": True, "codenotary": "x"}
    assert r(best, apparmor_profile=True) == 8  # 5+1+2+1 = 9, clamped


def test_breakdown_explains_result():
    rating, breakdown = rating_security({"ingress": True, "host_network": True})
    assert rating == 6
    assert 5 + sum(b["modifier"] for b in breakdown) == rating


if __name__ == "__main__":
    import sys

    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as err:
                failures += 1
                print(f"FAIL {name}: {err}")
    sys.exit(1 if failures else 0)

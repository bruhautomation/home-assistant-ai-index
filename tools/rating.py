#!/usr/bin/env python3
"""Home Assistant add-on security rating, computed from an add-on's config.

This is a line-for-line port of the Supervisor's own algorithm:

    home-assistant/supervisor @ 64961ef9d19e934594746b551201b1922f5a4ea3
    supervisor/apps/utils.py, rating_security(), lines 19-86
    https://github.com/home-assistant/supervisor/blob/64961ef9d19e934594746b551201b1922f5a4ea3/supervisor/apps/utils.py#L19-L86

The scale is 1 (least confined) to 8 (most confined), starting at 5. We render
this number because it is Home Assistant's published metric computed by Home
Assistant's arithmetic — the index adds no scoring of its own.

Inputs are the raw keys of the add-on's config.yaml/config.json plus one fact
the config alone can't tell you: whether the add-on ships a custom AppArmor
profile (an apparmor.txt next to the config).
"""

from __future__ import annotations

# Privileges the Supervisor treats as rating-relevant
# (supervisor/docker/const.py Capabilities used in rating_security)
RISKY_CAPABILITIES = {
    "BPF",
    "CHECKPOINT_RESTORE",
    "DAC_READ_SEARCH",
    "NET_ADMIN",
    "NET_RAW",
    "PERFMON",
    "SYS_ADMIN",
    "SYS_MODULE",
    "SYS_PTRACE",
    "SYS_RAWIO",
}


def rating_security(config: dict, has_apparmor_profile: bool = False) -> tuple[int, list[dict]]:
    """Return (rating, breakdown) for an add-on config.

    breakdown is a list of {"modifier": int, "reason": str, "key": str} for
    every rule that fired, so the arithmetic can be shown, not just the result.
    """
    rating = 5
    breakdown: list[dict] = []

    def apply(modifier: int, key: str, reason: str) -> None:
        nonlocal rating
        rating += modifier
        breakdown.append({"modifier": modifier, "key": key, "reason": reason})

    # AppArmor: config `apparmor: false` disables it; a shipped apparmor.txt
    # gives the add-on a custom profile. Default (True, no profile) is neutral.
    if config.get("apparmor", True) is False:
        apply(-1, "apparmor", "AppArmor disabled")
    elif has_apparmor_profile:
        apply(+1, "apparmor", "custom AppArmor profile shipped")

    # Home Assistant login & ingress
    if config.get("ingress", False):
        apply(+2, "ingress", "UI served through authenticated ingress")
    elif config.get("auth_api", False):
        apply(+1, "auth_api", "uses Home Assistant authentication API")

    # Signed images (codenotary signer configured)
    if config.get("codenotary"):
        apply(+1, "codenotary", "container image is signed")

    # Privileged capabilities / kernel modules
    privileged = set(config.get("privileged", []) or [])
    if privileged & RISKY_CAPABILITIES or config.get("kernel_modules", False):
        apply(-1, "privileged", "requests privileged kernel capabilities")

    # Supervisor API role
    role = config.get("hassio_role", "default")
    if role == "manager":
        apply(-1, "hassio_role", "Supervisor API access with manager role")
    elif role == "admin":
        apply(-2, "hassio_role", "Supervisor API access with admin role")

    # Host networking
    if config.get("host_network", False):
        apply(-1, "host_network", "runs on the host network")

    # Host PID namespace
    if config.get("host_pid", False):
        apply(-2, "host_pid", "shares the host PID namespace")

    # Host UTS namespace (only rating-relevant combined with SYS_ADMIN)
    if config.get("host_uts", False) and "SYS_ADMIN" in privileged:
        apply(-1, "host_uts", "host UTS namespace with SYS_ADMIN")

    # Docker API or full access: floor to 1 regardless of everything above
    if config.get("docker_api", False) or config.get("full_access", False):
        rating = 1
        breakdown.append(
            {
                "modifier": 0,
                "key": "docker_api" if config.get("docker_api") else "full_access",
                "reason": "Docker API / full hardware access — rating forced to 1",
            }
        )
        return 1, breakdown

    return max(min(8, rating), 1), breakdown


if __name__ == "__main__":
    import json
    import sys

    import yaml

    with open(sys.argv[1], encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    value, why = rating_security(cfg, has_apparmor_profile="--apparmor" in sys.argv)
    print(json.dumps({"rating": value, "breakdown": why}, indent=2))

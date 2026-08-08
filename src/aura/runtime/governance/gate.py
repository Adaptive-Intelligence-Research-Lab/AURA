"""
Governance Engine — AURA-012

Minimal governance for v0.1.
Supports allow/deny decisions based on capability-level policies.

Full policy enforcement (authentication, authorization, 
privacy controls, audit trails) will be implemented
in later versions.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GovernanceDecision:
    """Result of a governance check."""
    allowed: bool
    reason: str | None = None


class GovernanceGate:
    """
    Minimal governance gate for AURA Runtime Core v0.1.
    
    The gate applies a simple allow/deny policy:
    - Default policy (allow or deny)
    - Explicit capability denials override allow
    - Explicit capability allows override deny (takes highest priority)

    Denied actions SHALL NOT reach the capability provider.
    
    The gate SHALL NOT make domain-specific decisions.
    """

    def __init__(self, default_policy: str = "allow"):
        """
        Initialize the governance gate.

        Args:
            default_policy: Either "allow" or "deny".
                            Defaults to "allow".
        """
        if default_policy not in ("allow", "deny"):
            raise ValueError(
                f"Invalid policy: {default_policy}. Must be 'allow' or 'deny'."
            )
        self.default_policy = default_policy
        self._denied_capabilities: set[str] = set()
        self._allowed_capabilities: set[str] = set()

    def deny_capability(self, capability_id: str) -> None:
        """
        Explicitly deny a specific capability.

        Denied capabilities will never be allowed,
        regardless of the default policy.

        Args:
            capability_id: The capability to deny
        """
        self._denied_capabilities.add(capability_id)
        self._allowed_capabilities.discard(capability_id)
        logger.info(f"Capability denied: {capability_id}")

    def allow_capability(self, capability_id: str) -> None:
        """
        Explicitly allow a specific capability.

        Allowed capabilities will always be allowed,
        regardless of the default policy.
        This takes precedence over deny.

        Args:
            capability_id: The capability to allow
        """
        self._allowed_capabilities.add(capability_id)
        self._denied_capabilities.discard(capability_id)
        logger.info(f"Capability allowed: {capability_id}")

    def check(self, action) -> GovernanceDecision:
        """
        Check whether an action should be allowed.

        Decision logic (in priority order):
        1. Explicit allow list - allowed
        2. Explicit deny list - denied
        3. Default policy - allow/deny

        Args:
            action: The action to check (must have capability_id attribute)

        Returns:
            GovernanceDecision with allowed=True/False
        """
        cap_id = action.capability_id

        # Explicit allow takes highest priority
        if cap_id in self._allowed_capabilities:
            return GovernanceDecision(allowed=True)

        # Explicit deny takes precedence over default
        if cap_id in self._denied_capabilities:
            logger.warning(f"Governance DENIED capability: {cap_id}")
            return GovernanceDecision(
                allowed=False,
                reason=f"Capability explicitly denied: {cap_id}"
            )

        # Apply default policy
        if self.default_policy == "allow":
            return GovernanceDecision(allowed=True)
        else:
            return GovernanceDecision(
                allowed=False,
                reason="Default policy is deny"
            )

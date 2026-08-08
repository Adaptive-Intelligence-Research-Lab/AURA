"""
Capability Registry

The Capability Registry is responsible for capability discovery and resolution.

Required operations:
  - register()
  - unregister()
  - get()
  - resolve()
  - list()
  - contains()

Example:
  registry.resolve("core.echo")
  returns the corresponding capability provider.

The registry SHALL reject duplicate registrations unless 
explicit replacement is supported.
"""
from __future__ import annotations

import logging
from typing import Optional

from ...models.capabilities import CapabilityMetadata, CapabilityProvider

logger = logging.getLogger(__name__)


class CapabilityRegistry:
    """
    In-memory registry for capability providers.

    Provides discovery, registration, and resolution of capabilities.
    
    The registry maintains two internal mappings:
    - _providers: capability_id -> provider instance
    - _metadata: capability_id -> capability metadata
    
    All operations are synchronous except where noted.
    """

    def __init__(self):
        """Initialize an empty capability registry."""
        self._providers: dict[str, CapabilityProvider] = {}
        self._metadata: dict[str, CapabilityMetadata] = {}

    def register(self, provider: CapabilityProvider) -> None:
        """
        Register a capability provider.

        Args:
            provider: An instance implementing CapabilityProvider

        Raises:
            ValueError: If a capability with the same ID is already registered
            TypeError: If provider does not implement CapabilityProvider
        """
        # Validate provider implements the interface
        if not isinstance(provider, CapabilityProvider):
            raise TypeError(
                f"Expected CapabilityProvider instance, got {type(provider)}"
            )

        cap_id = provider.metadata.id

        if cap_id in self._providers:
            raise ValueError(
                f"Capability already registered: {cap_id}"
            )

        self._providers[cap_id] = provider
        self._metadata[cap_id] = provider.metadata
        logger.info(f"Registered capability: {cap_id}")

    def unregister(self, capability_id: str) -> bool:
        """
        Unregister a capability.

        Args:
            capability_id: The ID of the capability to unregister

        Returns:
            True if unregistered, False if not found
        """
        if capability_id not in self._providers:
            return False

        del self._providers[capability_id]
        del self._metadata[capability_id]
        logger.info(f"Unregistered capability: {capability_id}")
        return True

    def get(self, capability_id: str) -> Optional[CapabilityProvider]:
        """
        Get a capability provider by ID.

        Args:
            capability_id: The capability identifier

        Returns:
            The registered provider, or None if not found
        """
        return self._providers.get(capability_id)

    def resolve(self, capability_id: str) -> CapabilityProvider:
        """
        Resolve a capability by ID.

        Args:
            capability_id: The capability identifier

        Returns:
            The registered capability provider

        Raises:
            KeyError: If capability is not registered
        """
        provider = self._providers.get(capability_id)
        if provider is None:
            raise KeyError(f"Capability not found: {capability_id}")
        return provider

    def list(self) -> list[str]:
        """
        List all registered capability IDs.

        Returns:
            List of registered capability IDs
        """
        return list(self._providers.keys())

    def contains(self, capability_id: str) -> bool:
        """
        Check if a capability is registered.

        Args:
            capability_id: The capability identifier

        Returns:
            True if registered, False otherwise
        """
        return capability_id in self._providers

    def get_metadata(self, capability_id: str) -> Optional[CapabilityMetadata]:
        """
        Get metadata for a registered capability.

        Args:
            capability_id: The capability identifier

        Returns:
            CapabilityMetadata, or None if not found
        """
        return self._metadata.get(capability_id)

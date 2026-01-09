"""Handlers for KubeTimer operator."""

from kubetimer.handlers.deployment import scan_and_delete_deployments

__all__ = ["scan_and_delete_deployments"]

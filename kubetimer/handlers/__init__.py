"""
Handlers for KubeTimer operator.

Exports:
- Index handler functions for each resource type
- Timer handlers for TTL scanning
- Registry functions for handler registration
"""

from kubetimer.handlers.deployment import (
    deployment_index_handler,
    scan_and_delete_deployments,
    scan_deployments_from_index,
)

from kubetimer.handlers.timer import (
    check_ttl_timer_handler,
    config_index_handler,
    config_changed_handler,
)

from kubetimer.handlers.registry import (
    init_memo,
    configure_memo,
    register_all_indexes,
    register_resource_indexes,
    is_index_registered_in_memo,
    get_registered_indexes_from_memo,
)

__all__ = [
    "deployment_index_handler",
    "scan_and_delete_deployments",
    "scan_deployments_from_index",
    "check_ttl_timer_handler",
    "config_index_handler",
    "config_changed_handler",
    "init_memo",
    "configure_memo",
    "register_all_indexes",
    "register_resource_indexes",
    "is_index_registered_in_memo",
    "get_registered_indexes_from_memo",
]

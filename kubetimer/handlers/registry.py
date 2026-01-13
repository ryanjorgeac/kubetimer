from typing import List, Set

import kopf

from kubetimer.config.k8s import KubeTimerConfig
from kubetimer.utils.logs import get_logger

logger = get_logger(__name__)


def init_memo(memo: kopf.Memo) -> None:
    if not hasattr(memo, 'registered_indexes'):
        memo.registered_indexes = set()
    if not hasattr(memo, 'enabled_resources'):
        memo.enabled_resources = set()
    if not hasattr(memo, 'config_loaded'):
        memo.config_loaded = False


def configure_memo(memo: kopf.Memo, config: KubeTimerConfig) -> None:
    memo.enabled_resources = set(config.enabled_resources)
    memo.annotation_key = config.annotation_key
    memo.dry_run = config.dry_run
    memo.timezone = config.timezone
    memo.namespaces = config.namespaces
    memo.config_loaded = True
    logger.info(
        "memo_configured",
        enabled_resources=list(memo.enabled_resources),
        memo=memo
    )


def is_index_registered_in_memo(memo: kopf.Memo, resource_type: str) -> bool:
    registered = getattr(memo, 'registered_indexes', set())
    return resource_type in registered



def register_all_indexes(
    memo: kopf.Memo,
    deployment_index_fn=None,
    pod_index_fn=None,
    statefulset_index_fn=None,
) -> List[str]:

    registered = []
    
    if deployment_index_fn:
        kopf.index('apps', 'v1', 'deployments')(deployment_index_fn)
        memo.registered_indexes.add('deployments')
        registered.append('deployments')
        logger.info("registered_deployment_index")

    if pod_index_fn:
        kopf.index('', 'v1', 'pods')(pod_index_fn)
        memo.registered_indexes.add('pods')
        registered.append('pods')
        logger.info("registered_pod_index")

    if statefulset_index_fn:
        kopf.index('apps', 'v1', 'statefulsets')(statefulset_index_fn)
        memo.registered_indexes.add('statefulsets')
        registered.append('statefulsets')
        logger.info("registered_statefulset_index")
    
    logger.info("all_indexes_registered", registered=registered)
    return registered


def register_resource_indexes(
    memo: kopf.Memo,
    index_handlers: dict
) -> List[str]:
    """
    Register indexes for resource types.
    
    DEPRECATED: Use register_all_indexes() instead.
    """
    return register_all_indexes(
        memo=memo,
        deployment_index_fn=index_handlers.get('deployments'),
        pod_index_fn=index_handlers.get('pods'),
        statefulset_index_fn=index_handlers.get('statefulsets'),
    )


def get_registered_indexes_from_memo(memo: kopf.Memo) -> Set[str]:
    """Get the set of registered indexes from memo."""
    return getattr(memo, 'registered_indexes', set()).copy()

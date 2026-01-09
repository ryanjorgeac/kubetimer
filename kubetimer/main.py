"""
KubeTimer Operator - Main entry point.

This operator watches KubeTimerConfig CRD resources and periodically scans
for Kubernetes resources (Deployments, Pods, ReplicaSets, etc.) with expired TTL
annotations, deleting them automatically.

Configuration:
- Environment variables (KUBETIMER_*): Operator-level settings
- CRD spec: Per-config user settings
"""

import kopf
from kubernetes import client, config

from kubetimer.config.settings import get_settings
from kubetimer.handlers.deployment import scan_and_delete_deployments
from kubetimer.utils.logging import setup_logging

# Load settings at module level so they're available for decorators
settings = get_settings()
logger = setup_logging()


def get_k8s_client() -> client.AppsV1Api:
    try:
        config.load_incluster_config()
        logger.info("loaded_incluster_config")
    except config.ConfigException:
        config.load_kube_config()
        logger.info("loaded_local_kube_config")
    return client.AppsV1Api()


@kopf.on.create('kubetimer.io', 'v1alpha1', 'kubetimerconfigs')
@kopf.on.update('kubetimer.io', 'v1alpha1', 'kubetimerconfigs')
def config_changed(spec, name, logger, **_):
    """
    This handler is called when a KubeTimerConfig resource is created or updated.
    It logs the configuration for visibility. The actual scanning happens
    in the timer handler below.
    
    Args:
        spec: The spec field from the KubeTimerConfig
        name: Name of the KubeTimerConfig resource
        logger: Kopf-provided logger (contextual)
    """
    logger.info(
        "config_updated",
        config_name=name,
        enabled_resources=spec.get('enabledResources', ['deployments']),
        annotation_key=spec.get('annotationKey', 'kubetimer.io/ttl'),
        check_interval=spec.get('checkIntervalSeconds', 60)
    )


@kopf.timer(
    'kubetimer.io', 'v1alpha1', 'kubetimerconfigs',
    interval=float(settings.check_interval),
    idle=10.0
)
def check_ttl_periodically(spec, name, logger, **_):
    """
    Periodically scan for resources with expired TTL.

    Args:
        spec: The KubeTimerConfig spec field
        name: Config resource name
        logger: Kopf-provided logger with context

    """
    enabled_resources = spec.get('enabledResources', ['deployments'])
    annotation_key = spec.get('annotationKey', 'kubetimer.io/ttl')
    dry_run = spec.get('dryRun', False)
    timezone_str = spec.get('timezone', 'UTC')
    
    namespaces_config = spec.get('namespaces', {})
    include_namespaces = namespaces_config.get('include', [])
    exclude_namespaces = namespaces_config.get('exclude', ['kube-system', 'kube-public', 'kube-node-lease'])
    
    logger.info(
        "starting_scan",
        config=name,
        include_namespaces=include_namespaces or "all",
        exclude_namespaces=exclude_namespaces,
        enabled_resources=enabled_resources,
        timezone=timezone_str,
        dry_run=dry_run
    )
    
    apps_v1 = get_k8s_client()

    if 'deployments' in enabled_resources:
        deleted_count = scan_and_delete_deployments(
            apps_v1=apps_v1,
            include_namespaces=include_namespaces,
            exclude_namespaces=exclude_namespaces,
            annotation_key=annotation_key,
            dry_run=dry_run,
            timezone_str=timezone_str
        )
        logger.info("deployments_processed", deleted=deleted_count)
    
    # Future: Add support for Pods and ReplicaSets
    # if 'pods' in enabled_resources:
    #     scan_and_delete_pods(apps_v1, scan_namespace, annotation_key, dry_run)
    # if 'replicasets' in enabled_resources:
    #     scan_and_delete_replicasets(apps_v1, scan_namespace, annotation_key, dry_run)


def main():
    settings = get_settings()
    
    logger.info(
        "starting_kubetimer",
        version="0.1.0",
        log_level=settings.log_level,
        annotation_key=settings.annotation_key,
        check_interval=settings.check_interval
    )

    kopf.run(
        standalone=True,
        loglevel=settings.log_level,
    )


if __name__ == "__main__":
    main()

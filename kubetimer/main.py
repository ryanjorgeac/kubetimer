"""
KubeTimer Operator - Main entry point.

This operator watches KubeTimerConfig CRD resources and periodically scans
for Kubernetes resources (Deployments, Pods, ReplicaSets, etc.) with expired TTL
annotations, deleting them automatically.
"""

import kopf
from kubernetes import client, config

from kubetimer.config.settings import get_settings
from kubetimer.handlers.deployment import scan_and_delete_deployments
from kubetimer.utils.logging import setup_logging

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


@kopf.timer('kubetimer.io', 'v1alpha1', 'kubetimerconfigs', interval=60.0, idle=10.0)
def check_ttl_periodically(spec, name, logger, **_):
    """
    Periodically scan for resources with expired TTL.

    Args:
        spec: The KubeTimerConfig spec field
        name: Config resource name
        logger: Kopf-provided logger with context
    """
    # Read configuration from CRD spec
    enabled_resources = spec.get('enabledResources', ['deployments'])
    annotation_key = spec.get('annotationKey', 'kubetimer.io/ttl')
    scan_namespace = spec.get('namespace', 'all')
    dry_run = spec.get('dryRun', False)
    
    logger.info(
        "starting_scan",
        config=name,
        namespace=scan_namespace,
        enabled_resources=enabled_resources,
        dry_run=dry_run
    )
    
    apps_v1 = get_k8s_client()

    if scan_namespace is None:
        scan_namespace = get_settings().default_namespace

    if 'deployments' in enabled_resources:
        deleted_count = scan_and_delete_deployments(
            apps_v1=apps_v1,
            namespace=scan_namespace,
            annotation_key=annotation_key,
            dry_run=dry_run
        )
        logger.info("deployments_processed", deleted=deleted_count)
    
    # Future: Add support for Pods and ReplicaSets
    # if 'pods' in enabled_resources:
    #     scan_and_delete_pods(apps_v1, scan_namespace, annotation_key, dry_run)
    # if 'replicasets' in enabled_resources:
    #     scan_and_delete_replicasets(apps_v1, scan_namespace, annotation_key, dry_run)


def main():
    """Entry point for the operator."""
    settings = get_settings()
    
    logger.info(
        "starting_kubetimer",
        version="0.1.0",
        log_level=settings.log_level,
        annotation_key=settings.annotation_key
    )

    kopf.run(
        standalone=True,
        loglevel=settings.log_level,
    )


if __name__ == "__main__":
    main()

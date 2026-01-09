"""
Deployment handler for KubeTimer operator.

Contains Kopf handlers for managing Deployment lifecycle based on TTL.
"""

from kubernetes import client

from kubetimer.utils.logging import get_logger
from kubetimer.utils.time_utils import is_ttl_expired, parse_ttl

logger = get_logger(__name__)


def scan_and_delete_deployments(
    apps_v1: client.AppsV1Api,
    namespace: str,
    annotation_key: str,
    dry_run: bool
) -> int:
    """
    Scan all Deployments in a namespace for expired TTL and delete them.
    
    Args:
        apps_v1: Kubernetes AppsV1Api client
        namespace: Kubernetes namespace to scan, or "all" for all namespaces
        annotation_key: The annotation key containing TTL value
        dry_run: If True, only log what would be deleted (don't actually delete)
    
    Returns:
        int: Number of deployments deleted (or would be deleted in dry-run)
    """

    if namespace == "all":
        deployments = apps_v1.list_deployment_for_all_namespaces()
        logger.info(
            "scanning_all_namespaces",
            deployment_count=len(deployments.items)
        )
    else:
        deployments = apps_v1.list_namespaced_deployment(namespace)
        logger.info(
            "scanning_namespace",
            namespace=namespace,
            deployment_count=len(deployments.items)
        )
    
    deleted_count = 0

    for deployment in deployments.items:
        annotations = deployment.metadata.annotations or {}

        if annotation_key not in annotations:
            continue
        
        ttl_value = annotations[annotation_key]
        
        try:
            ttl_datetime = parse_ttl(ttl_value)

            if is_ttl_expired(ttl_datetime):
                logger.warning(
                    "deployment_expired",
                    name=deployment.metadata.name,
                    namespace=deployment.metadata.namespace,
                    ttl=ttl_value,
                    dry_run=dry_run
                )
                
                if not dry_run:
                    apps_v1.delete_namespaced_deployment(
                        name=deployment.metadata.name,
                        namespace=deployment.metadata.namespace,
                        body=client.V1DeleteOptions()
                    )
                    logger.info(
                        "deployment_deleted",
                        name=deployment.metadata.name,
                        namespace=deployment.metadata.namespace
                    )
                
                deleted_count += 1
        
        except ValueError as e:
            logger.error(
                "invalid_ttl_format",
                name=deployment.metadata.name,
                namespace=deployment.metadata.namespace,
                ttl=ttl_value,
                error=str(e)
            )
    
    logger.info("scan_complete", deleted_count=deleted_count, dry_run=dry_run)
    return deleted_count

"""
Deployment handler for KubeTimer operator.

Contains Kopf handlers for managing Deployment lifecycle based on TTL.
"""

from typing import Any, Dict, List, Optional

import kopf
from kubernetes import client

from kubetimer.utils.logs import get_logger
from kubetimer.utils.time_utils import is_ttl_expired, parse_ttl

logger = get_logger(__name__)


def deployment_index_handler(
    name: str,
    namespace: str,
    meta: kopf.Meta,
    **_
) -> Optional[Dict[str, Any]]:
    annotations = meta.get('annotations', {})

    return {name: {
        'namespace': namespace,
        'annotations': annotations
    }}


def should_scan_namespace(
    namespace: str,
    include_namespaces: List[str],
    exclude_namespaces: List[str]
) -> bool:
    if namespace in exclude_namespaces:
        return False

    if not include_namespaces:
        return True

    return namespace in include_namespaces


def scan_and_delete_deployments(
    apps_v1: client.AppsV1Api,
    include_namespaces: List[str],
    exclude_namespaces: List[str],
    annotation_key: str,
    dry_run: bool,
    timezone_str: str = "UTC"
) -> int:
    
    deployments = apps_v1.list_deployment_for_all_namespaces()
    
    logger.info(
        "scanning_deployments",
        total_deployments=len(deployments.items),
        include_namespaces=include_namespaces or "all",
        exclude_namespaces=exclude_namespaces
    )
    
    deleted_count = 0
    scanned_count = 0

    for deployment in deployments.items:
        ns = deployment.metadata.namespace
        
        if not should_scan_namespace(ns, include_namespaces, exclude_namespaces):
            continue
        
        scanned_count += 1
        annotations = deployment.metadata.annotations or {}

        if annotation_key not in annotations:
            continue
        
        ttl_value = annotations[annotation_key]
        
        try:
            ttl_datetime = parse_ttl(ttl_value)

            if is_ttl_expired(ttl_datetime, timezone_str):
                logger.warning(
                    "deployment_expired",
                    name=deployment.metadata.name,
                    namespace=ns,
                    ttl=ttl_value,
                    dry_run=dry_run
                )
                
                if not dry_run:
                    apps_v1.delete_namespaced_deployment(
                        name=deployment.metadata.name,
                        namespace=ns,
                        body=client.V1DeleteOptions()
                    )
                    logger.info(
                        "deployment_deleted",
                        name=deployment.metadata.name,
                        namespace=ns
                    )
                
                deleted_count += 1
        
        except ValueError as e:
            logger.error(
                "invalid_ttl_format",
                name=deployment.metadata.name,
                namespace=ns,
                ttl=ttl_value,
                error=str(e)
            )
    
    logger.info(
        "scan_complete",
        scanned_deployments=scanned_count,
        deleted_count=deleted_count,
        dry_run=dry_run
    )
    return deleted_count


def scan_deployments_from_index(
    apps_v1: client.AppsV1Api,
    deployment_index: kopf.Index,
    include_namespaces: List[str],
    exclude_namespaces: List[str],
    annotation_key: str,
    dry_run: bool,
    timezone_str: str = "UTC"
) -> int:

    deleted_count = 0
    scanned_count = 0

    logger.info(
        "scanning_deployments_from_index",
        total_indexed=len(deployment_index),
        include_namespaces=include_namespaces or "all",
        exclude_namespaces=exclude_namespaces
    )

    for name, store in deployment_index.items():
        value = [v for v in store][0]
        ns = value['namespace']
        logger.info("checking_deployment", deployment=name, namespace=ns)
        if not should_scan_namespace(ns, include_namespaces, exclude_namespaces):
            continue
        
        scanned_count += 1
        annotations = value.get('annotations', {})

        if annotation_key not in annotations:
            continue
        
        ttl_value = annotations[annotation_key]
        
        try:
            ttl_datetime = parse_ttl(ttl_value)

            if is_ttl_expired(ttl_datetime, timezone_str):
                logger.warning(
                    "deployment_expired",
                    name=name,
                    namespace=ns,
                    ttl=ttl_value,
                    dry_run=dry_run
                )
                
                if not dry_run:
                    apps_v1.delete_namespaced_deployment(
                        name=name,
                        namespace=ns,
                        body=client.V1DeleteOptions()
                    )
                    logger.info("deployment_deleted", name=name, namespace=ns)
                
                deleted_count += 1
        
        except ValueError as e:
            logger.error(
                "invalid_ttl_format",
                name=name,
                namespace=ns,
                ttl=ttl_value,
                error=str(e)
            )
    
    logger.info(
        "scan_complete",
        scanned_deployments=scanned_count,
        deleted_count=deleted_count,
        dry_run=dry_run
    )
    return deleted_count

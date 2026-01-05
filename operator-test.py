import kopf
import kubernetes
from datetime import datetime, timezone
from kubernetes.client.rest import ApiException

TTL_ANNOTATION = "kubetimer.io/ttl"

@kopf.on.timer('apps', 'v1', 'deployments', interval=60.0)
def check_deployment_ttl(spec, meta, name, namespace, logger, **kwargs):
    """
    Runs every 60 seconds for EVERY Deployment in the cluster.
    Checks the annotation and deletes the deployment if time is up.
    """
    if meta.get('deletionTimestamp'):
        return
    
    annotations = meta.get('annotations', {})
    ttl_value = annotations.get(TTL_ANNOTATION)

    if not ttl_value:
        return

    try:
        expiry_time = datetime.fromisoformat(ttl_value.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)

        if now > expiry_time:
            logger.info(f"Time's up for {name}! Expiry: {expiry_time}, Now: {now}")

            api = kubernetes.client.AppsV1Api()
            try:
                api.delete_namespaced_deployment(name, namespace)
                return {"message": f"Deleted expired deployment {name}"}
            
            except ApiException as e:
                if e.status == 404:
                    logger.info(f"Deployment {name} was already deleted. Skipping.")
                    return None
                else:
                    raise e
        else:
            logger.info(f"Deployment {name} is still valid. Expiry: {expiry_time}, Now: {now}")
    except ValueError:
        logger.error(f"Invalid date format in {name}: {ttl_value}. Expected ISO8601 (e.g., 2026-01-25T15:00:00Z)")
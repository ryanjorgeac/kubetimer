import kopf
import asyncio
from kubernetes_asyncio import client, config
from kubernetes_asyncio.client.rest import ApiException
from datetime import datetime, timezone

TTL_ANNOTATION = "kubetimer.io/ttl"
_api_client = None

@kopf.on.startup()
async def startup(logger, **kwargs):
    global _api_client
    config.load_incluster_config() # config.load_kube_config()
    
    _api_client = client.ApiClient()
    logger.info("✅ Async Client Pool initialized.")

@kopf.on.cleanup()
async def cleanup(logger, **kwargs):
    global _api_client
    if _api_client:
        await _api_client.close()
        logger.info("🛑 Async Client Pool closed.")

@kopf.on.timer('deployments', interval=60.0, annotations={'kubetimer.io/ttl': kopf.PRESENT})
async def async_worker(meta, name, namespace, logger, **kwargs):
    if meta.get('deletionTimestamp'):
        return

    ttl_value = meta.get('annotations', {}).get(TTL_ANNOTATION)

    try:
        expiry = datetime.fromisoformat(ttl_value.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if now > expiry:
            logger.info(f"Time's up for {name}! Expiry: {expiry}, Now: {now}")
            api = client.AppsV1Api(_api_client)

            await api.delete_namespaced_deployment(name, namespace)
            return None
                
    except ValueError:
        logger.error(f"Invalid date format in {name}: {ttl_value}. Expected ISO8601 (e.g., 2026-01-25T15:00:00Z)")
    except ApiException as e:
        if e.status == 404:
            logger.info(f"Deployment {name} was already deleted. Skipping.")
            return None
        else:
            logger.error(f"❌ Failed to delete {name}: {e}")
            raise e
    except Exception as e:
        logger.error(f"🔥 Critical Logic Error on {name}: {e}")
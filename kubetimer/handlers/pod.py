from typing import Any, Dict


def pod_handler(
    name: str,
    namespace: str,
    meta: Dict[str, Any],
    **_
) -> None:
    pass


def pod_indexer(
    name: str,
    namespace: str,
    meta: Dict[str, Any],
    **_
) -> Dict[str, Any]:
    pass
import os
import sys
import tracemalloc
from typing import Any, Dict, List, Optional

from kubetimer.utils.logs import get_logger

logger = get_logger(__name__)

# Global state
_profiling_enabled = False
_baseline_snapshot: Optional[tracemalloc.Snapshot] = None


def is_profiling_enabled() -> bool:
    """Check if memory profiling is enabled via environment variable."""
    return os.environ.get('ENABLE_MEMORY_PROFILING', 'false').lower() == 'true'


def start_profiling(nframes: int = 25) -> bool:
    """
    Start memory profiling if enabled.
    
    Args:
        nframes: Number of stack frames to capture (more = more detail but more overhead)
    
    Returns:
        True if profiling was started, False otherwise
    """
    global _profiling_enabled, _baseline_snapshot
    
    if not is_profiling_enabled():
        logger.info("memory_profiling_disabled", hint="Set ENABLE_MEMORY_PROFILING=true to enable")
        return False
    
    if tracemalloc.is_tracing():
        logger.warning("memory_profiling_already_running")
        return True
    
    tracemalloc.start(nframes)
    _profiling_enabled = True
    _baseline_snapshot = tracemalloc.take_snapshot()
    
    logger.info("memory_profiling_started", nframes=nframes)
    return True


def stop_profiling() -> None:
    """Stop memory profiling and clear state."""
    global _profiling_enabled, _baseline_snapshot
    
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    
    _profiling_enabled = False
    _baseline_snapshot = None
    logger.info("memory_profiling_stopped")


def get_memory_snapshot() -> Dict[str, Any]:
    """
    Get current memory usage snapshot.
    
    Returns:
        Dict with current, peak, and traced memory stats
    """
    result = {
        "profiling_enabled": tracemalloc.is_tracing(),
        "process_memory_mb": _get_process_memory_mb(),
    }
    
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        result.update({
            "traced_current_mb": round(current / 1024 / 1024, 2),
            "traced_peak_mb": round(peak / 1024 / 1024, 2),
        })
    
    return result


def get_top_allocations(limit: int = 10, key_type: str = "lineno") -> List[Dict[str, Any]]:
    """
    Get top memory allocations by location.
    
    Args:
        limit: Number of top allocations to return
        key_type: How to group allocations - "lineno" (file:line) or "traceback" (full stack)
    
    Returns:
        List of dicts with file, line, size_mb for each top allocation
    """
    if not tracemalloc.is_tracing():
        return []
    
    snapshot = tracemalloc.take_snapshot()
    # Filter out tracemalloc's own allocations
    snapshot = snapshot.filter_traces([
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
        tracemalloc.Filter(False, tracemalloc.__file__),
    ])
    
    stats = snapshot.statistics(key_type)
    
    results = []
    for stat in stats[:limit]:
        frame = stat.traceback[0] if stat.traceback else None
        results.append({
            "file": frame.filename if frame else "unknown",
            "line": frame.lineno if frame else 0,
            "size_mb": round(stat.size / 1024 / 1024, 4),
            "count": stat.count,
        })
    
    return results


def get_memory_diff_from_baseline() -> List[Dict[str, Any]]:
    """
    Compare current memory to baseline snapshot (taken at start_profiling).
    
    Useful for identifying memory growth over time.
    
    Returns:
        List of allocations that grew since baseline
    """
    global _baseline_snapshot
    
    if not tracemalloc.is_tracing() or _baseline_snapshot is None:
        return []
    
    current = tracemalloc.take_snapshot()
    diff = current.compare_to(_baseline_snapshot, "lineno")
    
    results = []
    for stat in diff[:20]:  # Top 20 growing allocations
        if stat.size_diff > 0:  # Only show growth
            frame = stat.traceback[0] if stat.traceback else None
            results.append({
                "file": frame.filename if frame else "unknown",
                "line": frame.lineno if frame else 0,
                "size_diff_kb": round(stat.size_diff / 1024, 2),
                "count_diff": stat.count_diff,
            })
    
    return results


def print_memory_report() -> None:
    """Print a formatted memory report to the logger."""
    snapshot = get_memory_snapshot()
    
    logger.info("=" * 60)
    logger.info("MEMORY PROFILING REPORT")
    logger.info("=" * 60)
    logger.info("memory_snapshot", **snapshot)
    
    if tracemalloc.is_tracing():
        logger.info("-" * 40)
        logger.info("TOP 10 ALLOCATIONS BY LINE")
        logger.info("-" * 40)
        
        for alloc in get_top_allocations(limit=10):
            logger.info(
                "allocation",
                file=alloc["file"],
                line=alloc["line"],
                size_mb=alloc["size_mb"],
                count=alloc["count"]
            )
        
        diff = get_memory_diff_from_baseline()
        if diff:
            logger.info("-" * 40)
            logger.info("MEMORY GROWTH SINCE BASELINE")
            logger.info("-" * 40)
            for item in diff[:10]:
                logger.info("growth", **item)
    
    logger.info("=" * 60)


def _get_process_memory_mb() -> float:
    """Get total process memory using /proc/self/status (Linux) or sys.getsizeof fallback."""
    try:
        # Linux: read from /proc
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # VmRSS is in kB
                    return round(int(line.split()[1]) / 1024, 2)
    except (FileNotFoundError, PermissionError):
        pass
    
    # Fallback: very rough estimate
    return round(sys.getsizeof(sys.modules) / 1024 / 1024, 2)


# Convenience: auto-start if env var is set during import
if is_profiling_enabled():
    start_profiling()

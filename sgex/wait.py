import time


def timeout(n_calls: int, server_info: dict) -> int:
    if not server_info.get("wait"):
        return 0
    else:
        waits = []
        for k, v in server_info["wait"].items():
            if v:
                if n_calls <= v:
                    waits.append(int(k))
        if not waits:
            waits.append(max([int(k) for k in server_info["wait"].keys()]))
        return min(waits)


def make_hook(timeout: float = 1.0):
    def hook(response, *args, **kwargs):
        if not getattr(response, "from_cache", False):
            time.sleep(timeout)
        return response

    return hook

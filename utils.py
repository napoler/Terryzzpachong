import math

def format_bytes(bytes_val, decimals=2):
    """Formats bytes into a human-readable string (KB, MB, GB, etc.)."""
    if bytes_val is None or bytes_val == 0:
        return "0 Bytes"
    k = 1024
    dm = decimals if decimals >= 0 else 0
    sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    i = math.floor(math.log(bytes_val, k)) if bytes_val > 0 else 0
    return f"{bytes_val / (k**i):.{dm}f} {sizes[i]}"

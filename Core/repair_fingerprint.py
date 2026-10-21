"""Stable crash fingerprints for comparing isolated repair runs."""
import hashlib, re

def compute_fingerprint(analysis=None, raw_log=''):
    text = str(raw_log or '')
    # Prefer the last Caused by chain; stack frames are much more stable than timestamps.
    blocks = re.split(r'(?im)^\s*Caused by:\s*', text)
    source = blocks[-1] if len(blocks) > 1 else text
    frames = re.findall(r'^\s*at\s+([^\s(]+)', source, re.M)[:5]
    if not frames and analysis:
        frames = [str(x) for x in analysis.get('evidence', []) if 'Exception' in str(x)][:3]
    if not frames: return ''
    normalized = []
    for frame in frames:
        frame = re.sub(r':\d+', ':#', frame)
        frame = re.sub(r'0x[0-9a-f]+', '0x#', frame, flags=re.I)
        normalized.append(frame)
    return hashlib.sha256('\n'.join(normalized).encode()).hexdigest()[:8]

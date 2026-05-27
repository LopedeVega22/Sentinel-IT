import re


def derive_revert_command(command: str, blocked_ip: str = "") -> str:
    """Return a command that undoes the original only when it can be derived."""
    original = (command or "").strip()
    reverted = original

    if reverted:
        replacements = (
            (r'(?<!\S)-A(?!\S)', '-D'),
            (r'(?<!\S)-I(?!\S)', '-D'),
            (r'(?<!\S)--append(?!\S)', '--delete'),
            (r'(?<!\S)--insert(?!\S)', '--delete'),
        )
        for pattern, replacement in replacements:
            reverted = re.sub(pattern, replacement, reverted)

        reverted = re.sub(
            r'\bufw\s+(deny|reject|allow)\b',
            r'ufw delete \1',
            reverted,
        )

        if reverted != original:
            return reverted

        service_reverts = (
            (r'\bsystemctl\s+stop\b', 'systemctl start'),
            (r'\bsystemctl\s+start\b', 'systemctl stop'),
            (r'\bsystemctl\s+disable\b', 'systemctl enable'),
            (r'\bsystemctl\s+enable\b', 'systemctl disable'),
            (r'\bservice\s+(\S+)\s+stop\b', r'service \1 start'),
            (r'\bservice\s+(\S+)\s+start\b', r'service \1 stop'),
        )
        for pattern, replacement in service_reverts:
            service_reverted = re.sub(pattern, replacement, original)
            if service_reverted != original:
                return service_reverted

    return ""

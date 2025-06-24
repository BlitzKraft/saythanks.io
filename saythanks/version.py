def get_version():
    try:
        with open("version.txt") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"


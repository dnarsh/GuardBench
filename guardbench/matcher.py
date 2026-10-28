"""Location matcher: a comment is a hit when file matches and line is within +-TOLERANCE."""

TOLERANCE = 3


def norm(path):
    if not isinstance(path, str):
        return None
    p = path.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


def is_hit(comment, file, start, end, tol=TOLERANCE):
    if not isinstance(comment, dict):
        return False
    line = comment.get("line")
    if isinstance(line, bool) or not isinstance(line, int) or line < 1:
        return False
    got = norm(comment.get("file"))
    return got is not None and got == norm(file) and start - tol <= line <= end + tol

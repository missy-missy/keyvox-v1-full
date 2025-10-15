# backend/locked_files_store.py
# backend/locked_files_store.py
import os
import json
import shutil
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# =========================
# Public constants / knobs
# =========================
MAX_LOCKED_FILES = 20

# You can override these via env vars if needed
ENV_FILES_ROOT = "KEYVOX_USER_FILES_ROOT"   # where the real files are stored (moved/copied)
ENV_FILES_DB_ROOT = "KEYVOX_USER_FILES_DB"  # where per-user JSON metadata lives


# =========================
# Paths & Setup
# =========================
def _project_root() -> str:
    # <repo-root> where backend and frontend live
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _default_files_root() -> str:
    """
    Default to a sibling of the repo folder:
      <parent_of_repo>/keyvoxUserFiles
    Example:
      C:/Users/Admin/keyvox-v1           (repo)
      C:/Users/Admin/keyvoxUserFiles     (files)
    """
    parent_of_repo = os.path.dirname(_project_root())
    return os.path.join(parent_of_repo, "keyvoxUserFiles")

def _default_files_db_root() -> str:
    # <repo-root>/backend/user_files_db
    return os.path.join(os.path.dirname(__file__), "user_files_db")

def _files_root() -> str:
    return os.environ.get(ENV_FILES_ROOT, _default_files_root())

def _files_db_root() -> str:
    return os.environ.get(ENV_FILES_DB_ROOT, _default_files_db_root())

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _user_folder(username: str) -> str:
    folder = os.path.join(_files_root(), username)
    _ensure_dir(folder)
    return folder

def _user_files_json_path(username: str) -> str:
    root = _files_db_root()
    _ensure_dir(root)
    return os.path.join(root, f"{username}.json")

def _downloads_dir() -> str:
    """
    Best-effort path to the user's Downloads folder.
    Windows:  C:\\Users\\<user>\\Downloads
    macOS:    ~/Downloads
    Linux:    ~/Downloads
    Falls back to home if Downloads doesn't exist.
    """
    home = os.path.expanduser("~")
    downloads = os.path.join(home, "Downloads")
    return downloads if os.path.isdir(downloads) else home

def _collision_safe_path(dirpath: str, filename: str) -> str:
    """
    Return a path in dirpath that doesn't overwrite existing files by adding
    ' (1)', ' (2)', etc. before the extension.
    """
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(dirpath, filename)
    i = 1
    while os.path.exists(candidate):
        candidate = os.path.join(dirpath, f"{base} ({i}){ext}")
        i += 1
    return candidate

# =========================
# JSON I/O (per-user)
# =========================
def _load_user_files_db(username: str) -> Dict[str, Any]:
    """Per-user file metadata store: { "locked_files": [...] }"""
    path = _user_files_json_path(username)
    if not os.path.exists(path):
        return {"locked_files": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"locked_files": []}
    if not isinstance(data, dict):
        data = {"locked_files": []}
    if "locked_files" not in data or not isinstance(data["locked_files"], list):
        data["locked_files"] = []
    return data

def _save_user_files_db(username: str, db: Dict[str, Any]) -> None:
    path = _user_files_json_path(username)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# =========================
# Helpers
# =========================
def _safe_filename(name: str) -> str:
    """Sanitize filename while keeping the extension."""
    stem, ext = os.path.splitext(name)
    keep = "".join(c for c in stem if c.isalnum() or c in ("-", "_", " ")).strip() or "file"
    return keep + ext

def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def _hash_for_collision(src_path: str) -> str:
    """Short hash for disambiguating duplicates."""
    try:
        st = os.stat(src_path)
        basis = f"{src_path}|{st.st_size}|{int(st.st_mtime)}"
    except Exception:
        basis = src_path
    return hashlib.sha1(basis.encode("utf-8", errors="ignore")).hexdigest()[:7]

def _make_meta(stored_abs: str, original_abs: str) -> Dict[str, Any]:
    """Build a metadata dict; includes legacy 'path' for backward compatibility."""
    try:
        size_bytes = os.path.getsize(stored_abs)
    except Exception:
        size_bytes = None
    return {
        "name": os.path.basename(stored_abs),
        "stored_path": stored_abs,
        "path": stored_abs,               # legacy key so old UI keeps working
        "original_path": original_abs,
        "added_at": _timestamp(),
        "size_bytes": size_bytes,
    }


# =========================
# Public API (same function names you already use)
# =========================
def load_locked_files(username: str) -> List[Dict[str, Any]]:
    """
    Return the user's locked files from per-user JSON.
    Each item:
      {
        "name": "<filename.ext>",
        "stored_path": "<.../keyvoxUserFiles/<username>/<filename.ext>>",
        "path": "<same as stored_path (legacy)>",
        "original_path": "<original path before move/copy>",
        "added_at": "UTC_ISO",
        "size_bytes": <int or None>
      }
    """
    db = _load_user_files_db(username)
    return db.get("locked_files", [])

def save_locked_files(username: str, items: List[Dict[str, Any]]) -> None:
    """Overwrite the user's locked_files list in per-user JSON."""
    db = _load_user_files_db(username)
    db["locked_files"] = list(items or [])
    _save_user_files_db(username, db)

def append_locked_file(username: str, meta: Dict[str, Any]) -> None:
    """Append one metadata entry (no file ops)."""
    db = _load_user_files_db(username)
    files = db.get("locked_files", [])
    if len(files) >= MAX_LOCKED_FILES:
        raise ValueError(f"Limit reached ({MAX_LOCKED_FILES}) for user {username}")
    files.append(meta)
    db["locked_files"] = files
    _save_user_files_db(username, db)

def remove_locked_file_by_index(username: str, idx: int) -> Optional[Dict[str, Any]]:
    """
    Remove metadata entry by index and MOVE the stored file to the user's Downloads
    folder (instead of deleting).
    Returns the removed metadata, or None if idx invalid.
    """
    db = _load_user_files_db(username)
    files = db.get("locked_files", [])
    if not (0 <= idx < len(files)):
        return None

    removed = files.pop(idx)
    db["locked_files"] = files
    _save_user_files_db(username, db)

    spath = removed.get("stored_path") or removed.get("path")
    if spath and os.path.isfile(spath):
        try:
            dest_dir = _downloads_dir()
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = _collision_safe_path(dest_dir, os.path.basename(spath))
            shutil.move(spath, dest_path)
            # Optionally annotate where we moved it
            removed["moved_to"] = dest_path
        except Exception:
            # If move fails, we silently keep the file where it is
            pass

    return removed

def build_meta_for_existing_path(src_path: str) -> Dict[str, Any]:
    """
    Backward-compatible: describe an existing file (no copy/move).
    """
    if not src_path or not os.path.isfile(src_path):
        raise ValueError("Selected path is not an existing file.")
    apath = os.path.abspath(src_path)
    try:
        size_bytes = os.path.getsize(apath)
    except Exception:
        size_bytes = None
    return {
        "name": os.path.basename(apath),
        "stored_path": apath,     # legacy callers may treat this as "path"
        "path": apath,            # legacy
        "original_path": apath,
        "added_at": _timestamp(),
        "size_bytes": size_bytes,
    }

def relink_locked_file(username: str, idx: int, new_path: str) -> Dict[str, Any]:
    """
    Replace the entry at idx with metadata built from new_path (no copy/move).
    """
    files = load_locked_files(username)
    if not (0 <= idx < len(files)):
        raise IndexError("Index out of range.")
    meta = build_meta_for_existing_path(new_path)
    files[idx] = meta
    save_locked_files(username, files)
    return meta


# =========================
# New APIs (preferred)
# =========================
def add_and_copy_file(username: str, src_path: str) -> Dict[str, Any]:
    """
    Copy src_path into keyvoxUserFiles/<username>/ and record metadata.
    Returns the metadata entry.
    """
    if not username:
        raise ValueError("Username is required.")
    if not src_path or not os.path.isfile(src_path):
        raise ValueError("Selected path is not an existing file.")

    user_dir = _user_folder(username)
    base = _safe_filename(os.path.basename(src_path))
    dest = os.path.join(user_dir, base)

    # Disambiguate collisions
    if os.path.exists(dest):
        root, ext = os.path.splitext(base)
        dest = os.path.join(user_dir, f"{root}_{_hash_for_collision(src_path)}{ext}")

    _ensure_dir(os.path.dirname(dest))
    shutil.copy2(src_path, dest)

    meta = _make_meta(os.path.abspath(dest), os.path.abspath(src_path))
    append_locked_file(username, meta)
    return meta

def add_and_move_file(username: str, src_path: str) -> Dict[str, Any]:
    """
    MOVE src_path into keyvoxUserFiles/<username>/ and record metadata.
    Returns the metadata entry.
    """
    if not username:
        raise ValueError("Username is required.")
    if not src_path or not os.path.isfile(src_path):
        raise ValueError("Selected path is not an existing file.")

    user_dir = _user_folder(username)
    base = _safe_filename(os.path.basename(src_path))
    dest = os.path.join(user_dir, base)

    # Disambiguate collisions
    if os.path.exists(dest):
        root, ext = os.path.splitext(base)
        dest = os.path.join(user_dir, f"{root}_{_hash_for_collision(src_path)}{ext}")

    _ensure_dir(os.path.dirname(dest))
    shutil.move(src_path, dest)

    meta = _make_meta(os.path.abspath(dest), os.path.abspath(src_path))
    append_locked_file(username, meta)
    return meta


# =========================
# Optional: one-time migration from old users.json
# =========================
def migrate_from_users_json(username: str, users_json_path: Optional[str] = None) -> Tuple[int, int]:
    """
    If old users.json stored locked_files under the user, copy them into the new per-user store.
    Returns (migrated_count, skipped_count). Safe to run multiple times.
    """
    if users_json_path is None:
        users_json_path = os.path.join(os.path.dirname(__file__), "users.json")
    if not os.path.exists(users_json_path):
        return (0, 0)

    try:
        with open(users_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return (0, 0)

    # normalize shapes
    if isinstance(data, list) and data and isinstance(data[0], dict):
        data = data[0]
    if not isinstance(data, dict):
        return (0, 0)

    u = data.get(username)
    if not isinstance(u, dict):
        return (0, 0)

    old_items = u.get("locked_files") or []
    if not isinstance(old_items, list) or not old_items:
        return (0, 0)

    migrated = 0
    skipped = 0
    existing = load_locked_files(username)
    existing_paths = {e.get("stored_path") for e in existing if isinstance(e, dict)}

    for item in old_items:
        # accept either "path" or "stored_path" keys from legacy data
        p = (item or {}).get("path") or (item or {}).get("stored_path")
        if not p or not os.path.isfile(p):
            skipped += 1
            continue
        meta = add_and_copy_file(username, p)
        if meta.get("stored_path") in existing_paths:
            skipped += 1
        else:
            migrated += 1

    return (migrated, skipped)


__all__ = [
    "MAX_LOCKED_FILES",
    "load_locked_files",
    "save_locked_files",
    "append_locked_file",
    "remove_locked_file_by_index",
    "build_meta_for_existing_path",
    "relink_locked_file",
    "add_and_copy_file",
    "add_and_move_file",
    "migrate_from_users_json",
]


# # backend/locked_files_store.py

# import os
# import json
# from datetime import datetime
# from typing import List, Dict, Any, Optional

# # Maximum files a user can link in Manage Files
# MAX_LOCKED_FILES = 20


# # ---------- Paths ----------

# def _backend_dir() -> str:
#     """Absolute path to the backend folder (this file's directory)."""
#     return os.path.dirname(os.path.abspath(__file__))

# def _users_json_path() -> str:
#     """Absolute path to backend/users.json."""
#     return os.path.join(_backend_dir(), "users.json")


# # ---------- JSON I/O (robust to old/new shapes) ----------

# def _load_users_db() -> Dict[str, Any]:
#     """
#     Load users.json and normalize it to a dict keyed by username.
#     Older versions may have stored a list containing a single dict; this handles that.
#     """
#     path = _users_json_path()
#     if not os.path.exists(path):
#         return {}
#     try:
#         with open(path, "r", encoding="utf-8") as f:
#             data = json.load(f)
#     except Exception:
#         return {}

#     # Normalize: if it's a list like [ { ...users... } ], unwrap it
#     if isinstance(data, list) and data and isinstance(data[0], dict):
#         data = data[0]
#     if not isinstance(data, dict):
#         data = {}
#     return data

# def _save_users_db(db: Dict[str, Any]) -> None:
#     """
#     Save users.json in normalized dict form (not a list wrapper).
#     Preserves any unrelated user fields (full_name, email, etc.).
#     """
#     path = _users_json_path()
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(db, f, ensure_ascii=False, indent=4)

# def _ensure_user_node(db: Dict[str, Any], username: str) -> Dict[str, Any]:
#     """
#     Make sure db[username] exists and has a 'locked_files' list.
#     """
#     if username not in db or not isinstance(db[username], dict):
#         db[username] = {}
#     user = db[username]
#     if "locked_files" not in user or not isinstance(user["locked_files"], list):
#         user["locked_files"] = []
#     return user


# # ---------- Public API used by UI ----------

# def load_locked_files(username: str) -> List[Dict[str, Any]]:
#     """
#     Return the user's locked files list (may be empty).
#     Each item is a dict like:
#       {
#         "name": "<filename.ext>",
#         "path": "C:/full/original/path/filename.ext",
#         "added_at": "UTC_ISO_TIMESTAMP",
#         "size_bytes": <int or None>
#       }
#     """
#     db = _load_users_db()
#     user = db.get(username)
#     if not isinstance(user, dict):
#         return []
#     lf = user.get("locked_files")
#     return lf if isinstance(lf, list) else []

# def save_locked_files(username: str, items: List[Dict[str, Any]]) -> None:
#     """
#     Overwrite the user's locked_files with 'items'.
#     """
#     db = _load_users_db()
#     user = _ensure_user_node(db, username)
#     user["locked_files"] = list(items or [])
#     db[username] = user
#     _save_users_db(db)

# def append_locked_file(username: str, meta: Dict[str, Any]) -> None:
#     """
#     Append one file meta to the user's locked_files, respecting MAX_LOCKED_FILES.
#     """
#     db = _load_users_db()
#     user = _ensure_user_node(db, username)
#     if len(user["locked_files"]) >= MAX_LOCKED_FILES:
#         raise ValueError(f"Limit reached ({MAX_LOCKED_FILES}) for user {username}")
#     user["locked_files"].append(meta)
#     db[username] = user
#     _save_users_db(db)

# def remove_locked_file_by_index(username: str, idx: int) -> Optional[Dict[str, Any]]:
#     """
#     Remove and return the file meta at 'idx'. Returns None if out of range.
#     """
#     db = _load_users_db()
#     user = _ensure_user_node(db, username)
#     items = user["locked_files"]
#     if 0 <= idx < len(items):
#         removed = items.pop(idx)
#         db[username] = user
#         _save_users_db(db)
#         return removed
#     return None

# def build_meta_for_existing_path(src_path: str) -> Dict[str, Any]:
#     """
#     Validate and describe an existing file on disk; DO NOT copy it.
#     Returns the metadata dict stored in users.json.
#     """
#     if not src_path or not os.path.isfile(src_path):
#         raise ValueError("Selected path is not an existing file.")
#     apath = os.path.abspath(src_path)
#     try:
#         size_bytes = os.path.getsize(apath)
#     except Exception:
#         size_bytes = None
#     return {
#         "name": os.path.basename(apath),
#         "path": apath,
#         "added_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
#         "size_bytes": size_bytes,
#     }

# def relink_locked_file(username: str, idx: int, new_path: str) -> Dict[str, Any]:
#     """
#     Replace the file at index 'idx' with metadata built from 'new_path'.
#     Useful if a linked file was moved/renamed outside the app.
#     Returns the new meta.
#     """
#     db = _load_users_db()
#     user = _ensure_user_node(db, username)
#     items = user["locked_files"]
#     if not (0 <= idx < len(items)):
#         raise IndexError("Index out of range.")

#     meta = build_meta_for_existing_path(new_path)
#     items[idx] = meta
#     db[username] = user
#     _save_users_db(db)
#     return meta


# __all__ = [
#     "MAX_LOCKED_FILES",
#     "load_locked_files",
#     "save_locked_files",
#     "append_locked_file",
#     "remove_locked_file_by_index",
#     "build_meta_for_existing_path",
#     "relink_locked_file",
# ]

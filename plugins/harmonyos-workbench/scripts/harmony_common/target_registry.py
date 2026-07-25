"""Project-scoped target bindings and exclusive leases."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterator


SCHEMA = "harmonyos.workbench.targets/v2"
LEGACY_SCHEMA = "harmonyos.workbench.targets/v1"
FINGERPRINT_FIELDS = (
    "kind",
    "uuid",
    "serial",
    "device_type",
    "device_model",
    "product_model",
    "api_version",
    "os_version",
    "cpu_arch",
    "single_screen",
    "double_screen",
    "instance_path",
    "image_root",
    "image_subpath",
)


class RegistryError(RuntimeError):
    """A target binding or lease invariant was violated."""


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime | None = None) -> str:
    return (value or now_utc()).isoformat()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def default_state_path() -> Path:
    override = os.environ.get("HARMONYOS_WORKBENCH_STATE", "")
    if override:
        candidate = Path(override).expanduser()
        if candidate.suffix == ".json":
            return candidate
        return candidate / "target-registry.json"
    return Path.home() / ".codex/state/harmonyos-workbench/target-registry.json"


def empty_state() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "updatedAt": iso(),
        "projects": {},
        "leases": {},
    }


class StateStore:
    def __init__(self, path: Path | None = None) -> None:
        self.uses_default_path = path is None
        self.path = (path or default_state_path()).expanduser().resolve()
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    @contextmanager
    def transaction(self, *, write: bool) -> Iterator[dict[str, Any]]:
        parent_existed = self.path.parent.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.uses_default_path or not parent_existed:
            self.path.parent.chmod(0o700)
        self.lock_path.touch(exist_ok=True)
        self.lock_path.chmod(0o600)
        with self.lock_path.open("r+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX if write else fcntl.LOCK_SH)
            state = self._read()
            try:
                yield state
                if write:
                    state["updatedAt"] = iso()
                    self._write(state)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return empty_state()
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RegistryError(f"target registry is unreadable: {self.path}: {error}") from error
        if state.get("schema") == LEGACY_SCHEMA:
            state = migrate_v1(state)
        if state.get("schema") != SCHEMA:
            raise RegistryError(
                f"unsupported target registry schema: {state.get('schema', 'missing')}"
            )
        state.setdefault("projects", {})
        state.setdefault("leases", {})
        return state

    def _write(self, state: dict[str, Any]) -> None:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            delete=False,
        ) as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temporary = Path(handle.name)
        temporary.replace(self.path)
        self.path.chmod(0o600)


def project_root_fingerprint(project_root: str) -> str:
    canonical = str(Path(project_root).expanduser().resolve())
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def migrate_v1(state: dict[str, Any]) -> dict[str, Any]:
    """Remove path and host metadata from the legacy registry shape."""
    for project in state.get("projects", {}).values():
        raw_root = str(project.pop("root", "") or "")
        project.setdefault(
            "rootFingerprint",
            project_root_fingerprint(raw_root) if raw_root else "",
        )
        project.setdefault("projectName", Path(raw_root).name if raw_root else "project")
    for lease in state.get("leases", {}).values():
        for field in ("projectRoot", "host", "pid", "token"):
            lease.pop(field, None)
    state["schema"] = SCHEMA
    return state


def fingerprint(target: dict[str, Any]) -> dict[str, str]:
    return {field: str(target.get(field, "") or "") for field in FINGERPRINT_FIELDS}


def fingerprint_digest(value: dict[str, Any]) -> str:
    payload = json.dumps(fingerprint(value), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def target_key(target: dict[str, Any]) -> str:
    kind = str(target.get("kind", ""))
    stable = str(target.get("uuid", "")) if kind == "emulator" else str(target.get("serial", ""))
    if not kind or not stable:
        raise RegistryError("target lacks a stable kind/uuid or kind/serial identity")
    return f"{kind}:{stable}"


def project_entry(
    state: dict[str, Any],
    project_id: str,
    project_root: str,
    *,
    create: bool,
) -> dict[str, Any]:
    projects = state.setdefault("projects", {})
    entry = projects.get(project_id)
    root_fingerprint = project_root_fingerprint(project_root)
    project_name = Path(project_root).expanduser().resolve().name
    if entry is None:
        if not create:
            raise RegistryError(f"project has no target bindings: {project_id}")
        entry = {
            "projectId": project_id,
            "projectName": project_name,
            "rootFingerprint": root_fingerprint,
            "bindings": {},
            "createdAt": iso(),
        }
        projects[project_id] = entry
    elif entry.get("rootFingerprint") != root_fingerprint:
        raise RegistryError(
            f"project id {project_id} is already associated with another project root"
        )
    return entry


def all_bindings(state: dict[str, Any]) -> Iterator[tuple[str, str, dict[str, Any]]]:
    for project_id, project in state.get("projects", {}).items():
        for role, binding in project.get("bindings", {}).items():
            yield project_id, role, binding


def allocated_ports(state: dict[str, Any]) -> set[int]:
    ports: set[int] = set()
    for _, _, binding in all_bindings(state):
        try:
            port = int(binding.get("hdcPort", 0))
        except (TypeError, ValueError):
            continue
        if port:
            ports.add(port)
    return ports


def allocate_port(
    state: dict[str, Any],
    *,
    externally_used: set[int] | None = None,
    preferred: int | None = None,
) -> int:
    used = allocated_ports(state) | (externally_used or set())
    if preferred is not None:
        if not 10000 <= preferred <= 16555:
            raise RegistryError("HDC port must be between 10000 and 16555")
        if preferred in used:
            raise RegistryError(f"HDC port {preferred} is already allocated")
        return preferred
    for port in range(12000, 16556):
        if port not in used:
            return port
    for port in range(10000, 12000):
        if port not in used:
            return port
    raise RegistryError("no free HDC port remains in 10000-16555")


def bind(
    state: dict[str, Any],
    *,
    project_id: str,
    project_root: str,
    role: str,
    target: dict[str, Any],
    hdc_port: int | None,
    accept_drift: bool = False,
) -> dict[str, Any]:
    key = target_key(target)
    project = project_entry(state, project_id, project_root, create=True)
    existing = project["bindings"].get(role)
    if existing and existing.get("targetKey") != key:
        lease = state.get("leases", {}).get(existing.get("targetKey", ""))
        if lease and not lease_expired(lease):
            raise RegistryError(f"role {role} has an active lease; release it before rebinding")
    for other_project, other_role, other in all_bindings(state):
        if other.get("targetKey") == key and (
            other_project != project_id or other_role != role
        ):
            raise RegistryError(
                f"{key} is pinned to {other_project}:{other_role}; it cannot be shared implicitly"
            )
        if hdc_port and int(other.get("hdcPort", 0) or 0) == hdc_port and (
            other_project != project_id or other_role != role
        ):
            raise RegistryError(
                f"HDC port {hdc_port} is pinned to {other_project}:{other_role}"
            )
    current_fingerprint = fingerprint(target)
    current_digest = fingerprint_digest(target)
    if existing and existing.get("targetKey") == key:
        old_digest = existing.get("fingerprintDigest", "")
        if old_digest and old_digest != current_digest and not accept_drift:
            raise RegistryError(
                "target specification changed; inspect drift and pass --accept-drift only after validation"
            )
    binding = {
        "role": role,
        "targetKey": key,
        "kind": target.get("kind"),
        "name": target.get("name", ""),
        "uuid": target.get("uuid", ""),
        "serial": target.get("serial", ""),
        "hdcPort": hdc_port,
        "fingerprint": current_fingerprint,
        "fingerprintDigest": current_digest,
        "runtimeSerial": existing.get("runtimeSerial", "") if existing else "",
        "createdAt": existing.get("createdAt", iso()) if existing else iso(),
        "updatedAt": iso(),
    }
    project["bindings"][role] = binding
    project["updatedAt"] = iso()
    return binding


def get_binding(
    state: dict[str, Any],
    *,
    project_id: str,
    project_root: str,
    role: str,
) -> dict[str, Any]:
    project = project_entry(state, project_id, project_root, create=False)
    binding = project.get("bindings", {}).get(role)
    if not binding:
        raise RegistryError(f"project role is not bound: {project_id}:{role}")
    return binding


def binding_drift(binding: dict[str, Any], target: dict[str, Any]) -> list[dict[str, str]]:
    expected = binding.get("fingerprint", {})
    current = fingerprint(target)
    changes: list[dict[str, str]] = []
    for field in FINGERPRINT_FIELDS:
        if str(expected.get(field, "")) != str(current.get(field, "")):
            changes.append(
                {
                    "field": field,
                    "expected": str(expected.get(field, "")),
                    "actual": str(current.get(field, "")),
                }
            )
    return changes


def lease_expired(lease: dict[str, Any], at: datetime | None = None) -> bool:
    try:
        return parse_time(str(lease.get("expiresAt", ""))) <= (at or now_utc())
    except (TypeError, ValueError):
        return True


def acquire(
    state: dict[str, Any],
    *,
    project_id: str,
    project_root: str,
    role: str,
    ttl_seconds: int,
) -> dict[str, Any]:
    binding = get_binding(
        state,
        project_id=project_id,
        project_root=project_root,
        role=role,
    )
    ttl = max(60, min(ttl_seconds, 86400))
    key = binding["targetKey"]
    current = state.setdefault("leases", {}).get(key)
    if current and not lease_expired(current) and current.get("projectId") != project_id:
        raise RegistryError(
            f"{key} is leased by {current.get('projectId')} until {current.get('expiresAt')}"
        )
    acquired_at = current.get("acquiredAt", iso()) if current else iso()
    lease = {
        "targetKey": key,
        "projectId": project_id,
        "role": role,
        "acquiredAt": acquired_at,
        "heartbeatAt": iso(),
        "expiresAt": iso(now_utc() + timedelta(seconds=ttl)),
    }
    state["leases"][key] = lease
    return lease


def require_active_lease(
    state: dict[str, Any],
    *,
    project_id: str,
    binding: dict[str, Any],
) -> dict[str, Any]:
    lease = state.get("leases", {}).get(binding.get("targetKey", ""))
    if not lease:
        raise RegistryError("target has no active lease; run acquire first")
    if lease_expired(lease):
        raise RegistryError(
            f"target lease expired at {lease.get('expiresAt')}; renew it before device operations"
        )
    if lease.get("projectId") != project_id:
        raise RegistryError(f"target is leased by another project: {lease.get('projectId')}")
    return lease


def release(
    state: dict[str, Any],
    *,
    project_id: str,
    binding: dict[str, Any],
) -> dict[str, Any]:
    key = binding["targetKey"]
    lease = state.get("leases", {}).get(key)
    if not lease:
        return {"status": "already_released", "targetKey": key}
    if lease.get("projectId") != project_id:
        raise RegistryError(f"cannot release lease owned by {lease.get('projectId')}")
    state["leases"].pop(key, None)
    return {"status": "released", "targetKey": key}


def unbind(
    state: dict[str, Any],
    *,
    project_id: str,
    project_root: str,
    role: str,
) -> dict[str, Any]:
    project = project_entry(state, project_id, project_root, create=False)
    binding = get_binding(
        state,
        project_id=project_id,
        project_root=project_root,
        role=role,
    )
    lease = state.get("leases", {}).get(binding["targetKey"])
    if lease and not lease_expired(lease):
        raise RegistryError("release the active lease before unbinding")
    project["bindings"].pop(role, None)
    if not project["bindings"]:
        state["projects"].pop(project_id, None)
    return binding


def set_runtime_serial(
    state: dict[str, Any],
    *,
    project_id: str,
    project_root: str,
    role: str,
    serial: str,
) -> dict[str, Any]:
    binding = get_binding(
        state,
        project_id=project_id,
        project_root=project_root,
        role=role,
    )
    binding["runtimeSerial"] = serial
    binding["updatedAt"] = iso()
    return binding


def registry_issues(state: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    keys: dict[str, list[str]] = {}
    ports: dict[int, list[str]] = {}
    for project_id, role, binding in all_bindings(state):
        owner = f"{project_id}:{role}"
        keys.setdefault(str(binding.get("targetKey", "")), []).append(owner)
        port = int(binding.get("hdcPort", 0) or 0)
        if port:
            ports.setdefault(port, []).append(owner)
    for key, owners in keys.items():
        if key and len(owners) > 1:
            issues.append(
                {"severity": "error", "code": "duplicate_target_binding", "value": key, "owners": owners}
            )
    for port, owners in ports.items():
        if len(owners) > 1:
            issues.append(
                {"severity": "error", "code": "duplicate_hdc_port", "value": port, "owners": owners}
            )
    for key, lease in state.get("leases", {}).items():
        if lease_expired(lease):
            issues.append(
                {
                    "severity": "warning",
                    "code": "expired_lease",
                    "value": key,
                    "owner": lease.get("projectId", ""),
                    "expiredAt": lease.get("expiresAt", ""),
                }
            )
    return issues

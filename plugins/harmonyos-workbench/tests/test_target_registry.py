from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harmony_common.target_registry import (  # noqa: E402
    RegistryError,
    StateStore,
    acquire,
    allocate_port,
    bind,
    binding_drift,
    get_binding,
    release,
    require_active_lease,
    unbind,
)


def target(name: str, uuid: str, screen: str = "1260x2720") -> dict[str, object]:
    return {
        "kind": "emulator",
        "name": name,
        "uuid": uuid,
        "serial": "",
        "device_type": "phone",
        "device_model": "Pura",
        "product_model": "Phone",
        "api_version": "20",
        "os_version": "6.0",
        "cpu_arch": "arm64",
        "single_screen": screen,
        "double_screen": "",
        "instance_path": f"/fixtures/{name}",
        "image_root": "/fixtures/images",
        "image_subpath": "phone",
    }


class TargetRegistryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp.name) / "registry.json"
        self.store = StateStore(self.state_path)
        self.a = target("phone-a", "uuid-a")
        self.b = target("phone-b", "uuid-b")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_projects_get_distinct_targets_and_ports(self) -> None:
        with self.store.transaction(write=True) as state:
            first_port = allocate_port(state, preferred=12001)
            first = bind(
                state,
                project_id="project-a",
                project_root="/projects/a",
                role="primary",
                target=self.a,
                hdc_port=first_port,
            )
            second_port = allocate_port(state, preferred=12002)
            second = bind(
                state,
                project_id="project-b",
                project_root="/projects/b",
                role="primary",
                target=self.b,
                hdc_port=second_port,
            )
        self.assertNotEqual(first["targetKey"], second["targetKey"])
        self.assertNotEqual(first["hdcPort"], second["hdcPort"])

    def test_cross_project_target_reuse_is_blocked(self) -> None:
        with self.store.transaction(write=True) as state:
            bind(
                state,
                project_id="project-a",
                project_root="/projects/a",
                role="primary",
                target=self.a,
                hdc_port=12001,
            )
            with self.assertRaisesRegex(RegistryError, "cannot be shared"):
                bind(
                    state,
                    project_id="project-b",
                    project_root="/projects/b",
                    role="primary",
                    target=self.a,
                    hdc_port=12002,
                )

    def test_duplicate_port_is_blocked(self) -> None:
        with self.store.transaction(write=True) as state:
            bind(
                state,
                project_id="project-a",
                project_root="/projects/a",
                role="primary",
                target=self.a,
                hdc_port=12001,
            )
            with self.assertRaisesRegex(RegistryError, "HDC port 12001"):
                bind(
                    state,
                    project_id="project-b",
                    project_root="/projects/b",
                    role="primary",
                    target=self.b,
                    hdc_port=12001,
                )

    def test_active_lease_is_required_and_released_explicitly(self) -> None:
        with self.store.transaction(write=True) as state:
            binding = bind(
                state,
                project_id="project-a",
                project_root="/projects/a",
                role="primary",
                target=self.a,
                hdc_port=12001,
            )
            with self.assertRaisesRegex(RegistryError, "no active lease"):
                require_active_lease(state, project_id="project-a", binding=binding)
            lease = acquire(
                state,
                project_id="project-a",
                project_root="/projects/a",
                role="primary",
                ttl_seconds=600,
            )
            self.assertEqual(
                require_active_lease(
                    state,
                    project_id="project-a",
                    binding=binding,
                )["expiresAt"],
                lease["expiresAt"],
            )
            with self.assertRaisesRegex(RegistryError, "release the active lease"):
                unbind(
                    state,
                    project_id="project-a",
                    project_root="/projects/a",
                    role="primary",
                )
            release(state, project_id="project-a", binding=binding)
            removed = unbind(
                state,
                project_id="project-a",
                project_root="/projects/a",
                role="primary",
            )
            self.assertEqual(removed["targetKey"], "emulator:uuid-a")

    def test_specification_drift_is_detected(self) -> None:
        with self.store.transaction(write=True) as state:
            binding = bind(
                state,
                project_id="project-a",
                project_root="/projects/a",
                role="primary",
                target=self.a,
                hdc_port=12001,
            )
            changed = target("phone-a", "uuid-a", screen="1080x2340")
            drift = binding_drift(binding, changed)
        self.assertEqual([item["field"] for item in drift], ["single_screen"])

    def test_state_is_durable_json(self) -> None:
        with self.store.transaction(write=True) as state:
            bind(
                state,
                project_id="project-a",
                project_root="/projects/a",
                role="primary",
                target=self.a,
                hdc_port=12001,
            )
        decoded = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(decoded["schema"], "harmonyos.workbench.targets/v2")
        self.assertNotIn("root", decoded["projects"]["project-a"])
        self.assertIn("rootFingerprint", decoded["projects"]["project-a"])
        with self.store.transaction(write=False) as state:
            binding = get_binding(
                state,
                project_id="project-a",
                project_root="/projects/a",
                role="primary",
            )
        self.assertEqual(binding["uuid"], "uuid-a")
        self.assertEqual(self.state_path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.store.lock_path.stat().st_mode & 0o777, 0o600)

    def test_v1_state_migrates_without_private_host_metadata(self) -> None:
        legacy = {
            "schema": "harmonyos.workbench.targets/v1",
            "updatedAt": "2026-01-01T00:00:00+00:00",
            "projects": {
                "project-a": {
                    "projectId": "project-a",
                    "root": "/private/fixture/project-a",
                    "bindings": {},
                    "createdAt": "2026-01-01T00:00:00+00:00",
                }
            },
            "leases": {
                "emulator:uuid-a": {
                    "targetKey": "emulator:uuid-a",
                    "projectId": "project-a",
                    "projectRoot": "/private/fixture/project-a",
                    "role": "primary",
                    "token": "legacy-token",
                    "host": "private-host",
                    "pid": 1234,
                    "acquiredAt": "2026-01-01T00:00:00+00:00",
                    "heartbeatAt": "2026-01-01T00:00:00+00:00",
                    "expiresAt": "2026-01-01T00:10:00+00:00",
                }
            },
        }
        self.state_path.write_text(json.dumps(legacy), encoding="utf-8")
        with self.store.transaction(write=True) as state:
            self.assertEqual(state["schema"], "harmonyos.workbench.targets/v2")
        rendered = self.state_path.read_text(encoding="utf-8")
        for private_value in (
            "/private/fixture/project-a",
            "legacy-token",
            "private-host",
            '"pid"',
        ):
            self.assertNotIn(private_value, rendered)


if __name__ == "__main__":
    unittest.main()

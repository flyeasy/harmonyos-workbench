# Contributing

Thanks for improving HarmonyOS Workbench.

## Before opening a pull request

1. Keep each capability under the `harmonyos-*` naming family and preserve the shared phase contract.
2. Put reusable runtime code in `scripts/harmony_common/` instead of copying logic between skills.
3. Keep target selection project-scoped. Never fall back to an arbitrary connected target.
4. Do not add real device identifiers, local absolute paths, credentials, signing material or captured private UI.
5. Distinguish official/public platform sources from project experience and state the verification date for version-sensitive claims.
6. Add or update tests for behavior changes.

Run:

```bash
cd plugins/harmonyos-workbench
python3 -m unittest discover -s tests -v
```

Also validate every changed Skill and the plugin manifest with the current Codex `skill-creator` and `plugin-creator` validators.

## Third-party material

Do not copy third-party text, code, images, fonts or brand assets without a compatible license and required attribution. Modified Apache-2.0 source files must retain existing notices and carry a prominent modification notice.

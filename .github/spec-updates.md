# Automated spec updates

The daily `update-specs.yml` workflow reads `spec-updates.json`, updates every
configured spec, validates every `*.spec` file in the repository, and commits
changed specs. Packages that are not listed in the manifest are still
validated, but are not modified.

## Supported update types

### `github-release`

Selects the greatest numeric version from the first 100 GitHub tags matching
`tag_regex`. The expression must contain a named `version` capture group.

```json
{
  "name": "example",
  "type": "github-release",
  "repository": "owner/project",
  "spec": "example/example.spec",
  "tag_regex": "^v(?P<version>\\d+\\.\\d+\\.\\d+)$"
}
```

### `github-snapshot`

Pins the latest commit on `branch`. The RPM version is assembled with
`version_format`, whose available fields are `base_version`, `commit`,
`short_commit`, and `commit_date` (`YYYYMMDD`). The three commit-related macro
names identify `%global` declarations in the spec.

`base_version` can use a fixed `value`, or extract a named `version` group from
a file at the selected commit:

```json
{
  "name": "example-git",
  "type": "github-snapshot",
  "repository": "owner/project",
  "branch": "main",
  "spec": "example-git/example-git.spec",
  "commit_macro": "commit",
  "short_commit_macro": "shortcommit",
  "commit_date_macro": "commitdate",
  "base_version": {
    "file": "CMakeLists.txt",
    "regex": "project\\(Example VERSION (?P<version>\\d+\\.\\d+\\.\\d+)"
  },
  "version_format": "{base_version}~git{commit_date}.{short_commit}"
}
```

Set `short_commit_length` to override the default length of seven characters.
If `base_version` is omitted, the updater retains the part of the current RPM
version before the first `~`.

Snapshot changelogs begin with the old and new abbreviated commits, followed
by the non-merge, non-bot commit subjects in oldest-to-newest order. At most 15
subjects are included by default; set `changelog_commit_limit` to change the
limit. Rewritten or otherwise non-linear history falls back to the commit-range
summary.

### `github-stable-release`

Works like `github-release`, but reads GitHub releases rather than tags and
ignores releases marked as drafts or prereleases. When updating, it converts
the top-level bullets from a `What's Changed`, `What is Changed`, `Changes`,
`Change`, or `Notable Changes` section into wrapped, plain-text RPM changelog
entries. Nested bullets and later sections such as support or download
instructions are ignored. If no suitable bullets exist, the updater adds a
generic update entry.

## Git submodules

Either update type can update source macros for Git submodules. Map each
submodule path to the corresponding RPM macro:

```json
"submodules": {
  "thirdparty/library": "library_commit"
}
```

The spec must contain a declaration such as `%global library_commit abc123`.
The updater reads the gitlink revision from the selected release or snapshot
and replaces the macro value.

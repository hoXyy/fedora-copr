#!/usr/bin/env python3
"""Update RPM specs from the declarative .github/spec-updates.json file."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".github" / "spec-updates.json"
BOT = "GitHub Actions <41898282+github-actions[bot]@users.noreply.github.com>"


def request_json(url: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "fedora-copr-spec-updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def request_text(url: str) -> str:
    headers = {"User-Agent": "fedora-copr-spec-updater"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode()


def github_api(package: dict[str, Any], path: str) -> Any:
    return request_json(f"https://api.github.com/repos/{package['repository']}{path}")


def replace_once(text: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"expected one match for {pattern!r}, found {count}")
    return updated


def match_group(pattern: str, text: str, group: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"pattern did not match: {pattern!r}")
    try:
        return match.group(group)
    except IndexError as error:
        raise RuntimeError(f"pattern lacks the named group {group!r}") from error


def set_spec_version(text: str, version: str) -> str:
    return replace_once(text, r"^Version:\s+\S+", f"Version:        {version}")


def spec_version(text: str) -> str:
    return match_group(r"^Version:\s+(?P<version>\S+)", text, "version")


def set_macro(text: str, name: str, value: str) -> str:
    pattern = rf"^(%global {re.escape(name)}\s+)\S+"
    if not re.search(pattern, text, re.MULTILINE):
        raise RuntimeError(f"could not find RPM macro {name!r}")
    return replace_once(text, pattern, rf"\g<1>{value}")


def spec_macro(text: str, name: str) -> str:
    return match_group(
        rf"^%global\s+{re.escape(name)}\s+(?P<value>\S+)", text, "value"
    )


def add_changelog(text: str, version: str, messages: str | list[str]) -> str:
    today = dt.datetime.now(dt.UTC).date()
    if isinstance(messages, str):
        messages = [messages]
    details = "\n".join(
        textwrap.fill(
            f"- {message}",
            width=79,
            subsequent_indent="  ",
            break_long_words=False,
            break_on_hyphens=False,
        )
        for message in messages
    )
    entry = f"* {today:%a %b %d %Y} {BOT} - {version}-1\n{details}\n\n"
    return replace_once(text, r"^%changelog\n", f"%changelog\n{entry}")


def release_changelog(body: str, version: str) -> list[str]:
    """Turn the useful part of GitHub release Markdown into RPM bullets."""
    lines = body.replace("\r\n", "\n").splitlines()
    section_pattern = re.compile(
        r"^\s*(?:#{1,6}\s+|\*\*)"
        r"(?:notable\s+)?(?:what(?:'s| is)\s+)?changes?"
        r"(?:\*\*)?:?\s*$",
        re.I,
    )
    section_start = next(
        (
            index + 1
            for index, line in enumerate(lines)
            if section_pattern.fullmatch(line)
        ),
        None,
    )
    if section_start is not None:
        lines = lines[section_start:]
        section_end = next(
            (
                index
                for index, line in enumerate(lines)
                if re.match(r"^\s*(?:#{1,6}\s+|\*\*[^*]+\*\*:?)\s*$", line)
            ),
            len(lines),
        )
        lines = lines[:section_end]

    bullets = []
    for line in lines:
        # Nested bullets are commonly asides, contributor lists, or other
        # detail that is too noisy for an RPM changelog.
        match = re.match(r"^[-*+]\s+(.+?)\s*$", line)
        if not match:
            continue
        item = match.group(1)
        item = re.sub(r"!\[[^]]*]\([^)]+\)", "", item)
        item = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", item)
        item = re.sub(r"<[^>]+>", "", item)
        item = re.sub(r"(?<!\w)[*_]{1,2}|[*_]{1,2}(?!\w)", "", item)
        item = item.replace("`", "")
        item = html.unescape(re.sub(r"\s+", " ", item)).strip(" -")
        if item and not item.casefold().startswith("full changelog"):
            bullets.append(item.replace("%", "%%"))

    return bullets or [f"Update to upstream stable release {version}"]


def snapshot_changelog(
    package: dict[str, Any], old_commit: str, new_commit: str
) -> list[str]:
    old_short = old_commit[: package.get("short_commit_length", 7)]
    new_short = new_commit[: package.get("short_commit_length", 7)]
    fallback = [f"Update upstream snapshot from {old_short} to {new_short}"]
    if old_commit == new_commit:
        return fallback

    try:
        comparison = github_api(package, f"/compare/{old_commit}...{new_commit}")
    except urllib.error.HTTPError as error:
        if error.code in {404, 409, 422}:
            return fallback
        raise
    if comparison.get("status") != "ahead":
        return fallback

    summaries = []
    for commit in comparison.get("commits", []):
        if len(commit.get("parents", [])) > 1:
            continue
        author = commit.get("author") or {}
        if author.get("type") == "Bot" or author.get("login", "").endswith("[bot]"):
            continue
        subject = re.sub(
            r"\s+", " ", commit["commit"]["message"].splitlines()[0]
        ).strip()
        if subject:
            summaries.append(f"{commit['sha'][:7]} {subject.replace('%', '%%')}")

    limit = package.get("changelog_commit_limit", 15)
    messages = fallback + summaries[:limit]
    omitted = len(summaries) - len(summaries[:limit])
    if omitted > 0:
        messages.append(f"Plus {omitted} additional upstream commits")
    return messages


def submodule_revisions(
    package: dict[str, Any], ref: str
) -> dict[str, str]:
    configured = package.get("submodules", {})
    if not configured:
        return {}

    encoded_ref = urllib.parse.quote(ref, safe="")
    tree = github_api(package, f"/git/trees/{encoded_ref}?recursive=1")
    revisions = {
        configured[entry["path"]]: entry["sha"]
        for entry in tree["tree"]
        if entry["path"] in configured and entry["type"] == "commit"
    }
    expected = set(configured.values())
    if revisions.keys() != expected:
        missing = expected - revisions.keys()
        raise RuntimeError(f"missing submodules: {', '.join(sorted(missing))}")
    return revisions


def apply_submodules(
    text: str, package: dict[str, Any], ref: str
) -> str:
    for macro, revision in submodule_revisions(package, ref).items():
        text = set_macro(text, macro, revision)
    return text


def apply_source_revision(
    text: str, package: dict[str, Any], commit: str
) -> str:
    if commit_macro := package.get("commit_macro"):
        text = set_macro(text, commit_macro, commit)
    if short_commit_macro := package.get("short_commit_macro"):
        length = package.get("short_commit_length", 7)
        text = set_macro(text, short_commit_macro, commit[:length])
    return text


def update_release(package: dict[str, Any], text: str) -> tuple[str, str]:
    tags = github_api(package, "/tags?per_page=100")
    candidates = []
    pattern = package["tag_regex"]
    for tag in tags:
        match = re.fullmatch(pattern, tag["name"])
        if match:
            version = match.group("version")
            numeric = tuple(int(part) for part in version.split("."))
            candidates.append((numeric, version, tag["commit"]["sha"]))
    if not candidates:
        raise RuntimeError("no tags matched tag_regex")

    _, version, commit = max(candidates)
    updated = set_spec_version(text, version)
    updated = apply_source_revision(updated, package, commit)
    updated = apply_submodules(updated, package, commit)
    return updated, f"Update to upstream release {version}"


def update_stable_release(
    package: dict[str, Any], text: str
) -> tuple[str, str | list[str]]:
    releases = github_api(package, "/releases?per_page=100")
    candidates = []
    pattern = package["tag_regex"]
    for release in releases:
        if release["draft"] or release["prerelease"]:
            continue
        tag = release["tag_name"]
        match = re.fullmatch(pattern, tag)
        if match:
            version = match.group("version")
            numeric = tuple(int(part) for part in version.split("."))
            candidates.append((numeric, version, tag, release.get("body") or ""))
    if not candidates:
        raise RuntimeError("no stable releases matched tag_regex")

    _, version, ref, body = max(candidates)
    encoded_ref = urllib.parse.quote(ref, safe="")
    commit = github_api(package, f"/commits/{encoded_ref}")["sha"]
    updated = set_spec_version(text, version)
    updated = apply_source_revision(updated, package, commit)
    updated = apply_submodules(updated, package, commit)
    return updated, release_changelog(body, version)


def snapshot_base_version(package: dict[str, Any], commit: str) -> str:
    source = package.get("base_version")
    if not source:
        return spec_version((ROOT / package["spec"]).read_text()).split("~", 1)[0]
    if "value" in source:
        return source["value"]

    repository = package["repository"]
    path = urllib.parse.quote(source["file"], safe="/")
    url = f"https://raw.githubusercontent.com/{repository}/{commit}/{path}"
    return match_group(source["regex"], request_text(url), "version")


def update_snapshot(
    package: dict[str, Any], text: str
) -> tuple[str, str | list[str]]:
    old_commit = spec_macro(text, package["commit_macro"])
    branch = urllib.parse.quote(package.get("branch", "main"), safe="")
    commit_data = github_api(package, f"/commits/{branch}")
    commit = commit_data["sha"]
    short_commit = commit[: package.get("short_commit_length", 7)]
    timestamp = commit_data["commit"]["committer"]["date"]
    commit_date = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime(
        "%Y%m%d"
    )
    base_version = snapshot_base_version(package, commit)
    version = package["version_format"].format(
        base_version=base_version,
        commit=commit,
        short_commit=short_commit,
        commit_date=commit_date,
    )

    updated = set_spec_version(text, version)
    updated = set_macro(updated, package["commit_macro"], commit)
    updated = set_macro(updated, package["short_commit_macro"], short_commit)
    updated = set_macro(updated, package["commit_date_macro"], commit_date)
    updated = apply_submodules(updated, package, commit)
    return updated, snapshot_changelog(package, old_commit, commit)


UPDATERS = {
    "github-release": update_release,
    "github-stable-release": update_stable_release,
    "github-snapshot": update_snapshot,
}


def update_package(package: dict[str, Any]) -> None:
    name = package["name"]
    spec = ROOT / package["spec"]
    original = spec.read_text()
    old_version = spec_version(original)
    try:
        updater = UPDATERS[package["type"]]
    except KeyError as error:
        raise RuntimeError(f"{name}: unsupported update type {package['type']!r}") from error

    updated, messages = updater(package, original)
    new_version = spec_version(updated)
    if updated == original:
        print(f"{name}: {new_version} is current")
        return

    spec.write_text(add_changelog(updated, new_version, messages))
    print(f"{name}: {old_version} -> {new_version}")


def main() -> None:
    config = json.loads(CONFIG.read_text())
    for package in config["packages"]:
        try:
            update_package(package)
        except Exception as error:
            raise RuntimeError(f"failed to update {package.get('name', '<unnamed>')}") from error


if __name__ == "__main__":
    main()

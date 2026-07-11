#!/usr/bin/env python3
"""Generate the deterministic Docs Explorer context benchmark corpus."""

import argparse
import hashlib
import json
import os
import random
import shutil
from pathlib import Path


MAX_FILE_BYTES = 1024 * 1024
RELATIONS_PER_ARTIFACT = 10


def artifact_id(index):
    return "bench-{0:04d}".format(index)


def frontmatter(index, artifact_count, include_heading):
    links = []
    for offset in range(1, RELATIONS_PER_ARTIFACT + 1):
        target = artifact_id((index + offset) % artifact_count)
        links.append("  - {{ to: {0}, rel: depends-on }}".format(target))
    heading = "# Benchmark artifact {0}\n".format(index) if include_heading else ""
    marker = {
        0: "cyclic root fixture",
        1: "Unicode fixture",
        2: "maximum-sized fixture",
        3: "empty-body fixture",
        4: "small fixture",
        5: "high-degree relationship fixture",
    }.get(index, "standard fixture")
    return (
        "---\n"
        "id: {id}\n"
        'title: "Benchmark Artifact {index}"\n'
        "type: knowledge\n"
        "status: accepted\n"
        'owner: "@benchmark"\n'
        'phase: "performance"\n'
        "tags: [docs-explorer, benchmark]\n"
        "links:\n"
        "{links}\n"
        "review-by: 2027-01-01\n"
        "review-suggested: []\n"
        "summary: >-\n"
        "  Deterministic {marker} used by the Docs Explorer context benchmark.\n"
        "---\n"
        "{heading}"
    ).format(
        id=artifact_id(index),
        index=index,
        links="\n".join(links),
        marker=marker,
        heading=heading,
    ).encode("utf-8")


def fill_bytes(length, unicode_fixture):
    if length <= 0:
        return b""
    if not unicode_fixture:
        return (b"grounding project memory architecture evidence\n" * (length // 47 + 1))[:length]
    pattern = "Gruesse, 世界, 🚀 - grounded project memory.\n".encode("utf-8")
    repeated = pattern * (length // len(pattern))
    return repeated + (b"u" * (length - len(repeated)))


def allocate_sizes(prefixes, total_bytes, seed):
    count = len(prefixes)
    fixed = {
        2: MAX_FILE_BYTES,
        3: len(prefixes[3]),
        4: max(4096, len(prefixes[4])),
    }
    sizes = [None] * count
    for index, size in fixed.items():
        sizes[index] = size
    variable = [index for index in range(count) if index not in fixed]
    random.Random(seed).shuffle(variable)
    remaining = total_bytes - sum(fixed.values())
    quotient, remainder = divmod(remaining, len(variable))
    for position, index in enumerate(variable):
        sizes[index] = quotient + (1 if position < remainder else 0)
    for index, size in enumerate(sizes):
        if size < len(prefixes[index]):
            raise ValueError("target size is smaller than frontmatter for {0}".format(artifact_id(index)))
        if size > MAX_FILE_BYTES:
            raise ValueError("target size exceeds the per-file limit for {0}".format(artifact_id(index)))
    if sum(sizes) != total_bytes:
        raise AssertionError("allocated corpus size does not match the requested total")
    return sizes


def generate(root, artifact_count, relationship_count, total_bytes, seed):
    if relationship_count != artifact_count * RELATIONS_PER_ARTIFACT:
        raise ValueError("relationship count must equal artifact count multiplied by 10")
    if artifact_count < RELATIONS_PER_ARTIFACT + 1:
        raise ValueError("artifact count must be at least 11")
    if root.exists():
        shutil.rmtree(str(root))
    root.mkdir(parents=True)
    prefixes = [
        frontmatter(index, artifact_count, include_heading=index != 3)
        for index in range(artifact_count)
    ]
    sizes = allocate_sizes(prefixes, total_bytes, seed)
    digest = hashlib.sha256()
    for index, prefix in enumerate(prefixes):
        payload = prefix + fill_bytes(sizes[index] - len(prefix), unicode_fixture=index == 1)
        path = root / "{0}.md".format(artifact_id(index))
        path.write_bytes(payload)
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(payload)
    return {
        "schemaVersion": "docs-context-benchmark-corpus/v1",
        "seed": seed,
        "rootId": artifact_id(0),
        "artifacts": artifact_count,
        "relationships": relationship_count,
        "admittedSourceBytes": total_bytes,
        "sha256": digest.hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--artifacts", type=int, default=2000)
    parser.add_argument("--relationships", type=int, default=20000)
    parser.add_argument("--bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--seed", type=int, default=20260710)
    args = parser.parse_args()
    manifest = generate(
        Path(os.path.abspath(args.root)),
        args.artifacts,
        args.relationships,
        args.bytes,
        args.seed,
    )
    print(json.dumps(manifest, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from functools import cached_property
from typing import TypedDict

from rich.console import Console

LOGGER_NAME = "config-diff"

console = Console()


@dataclass
class Config:
    json: bool
    filename1: str
    filename2: str

    @classmethod
    def from_args(cls) -> Config:
        parser = argparse.ArgumentParser(
            prog="Config diff tool",
        )
        parser.add_argument("-j", "--json", action="store_true")
        parser.add_argument("filename1")
        parser.add_argument("filename2")
        args = parser.parse_args()
        return Config(
            filename1=args.filename1, filename2=args.filename2, json=args.json
        )


class Logger:
    def __init__(self, quiet=False):
        if quiet:
            f = open(os.devnull, "w")
            self.ch = Console(file=f)
        f = open(f"{LOGGER_NAME}.log", "w+")
        self.fh = Console(stderr=True, file=f)

    def debug(self, msg: str):
        self.fh.log(f"DEBUG: {msg}")

    def info(self, msg: str):
        self.fh.log(f"INFO: {msg}")

    def warning(self, msg: str):
        self.fh.log(f"WARNING: {msg}")

    def error(self, msg: str):
        self.fh.log(f"ERROR: {msg}")


log = Logger()

Block = dict[str, "Block"]


class DiffField(TypedDict):
    type: str
    children: Diff


Diff = dict[str, DiffField]


def indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def diff(a: Block, b: Block) -> Diff:
    """Return a - b diff of block dictionaries"""
    result = {}
    all = set(a.keys()) | set(b.keys())
    for key in all:
        if key in a and key not in b:
            result[key] = {"type": "delete", "children": {}}
            continue
        if key in b and key not in a:
            result[key] = {"type": "create", "children": {}}
            continue
        children = diff(a.get(key, {}), b.get(key, {}))
        if len(children) > 0:
            result[key] = {"type": "update", "children": children}
    return result


def sort_func(item):
    t = item[1]["type"]
    key = item[0]
    if t == "delete":
        return "0" + key
    if t == "create":
        return "1" + key
    if t == "update":
        return "2" + key
    return key


def pprint_diff(diff: Diff, indent=0):
    for key, details in sorted(diff.items(), key=sort_func):
        if details["type"] == "update":
            print(" " * indent, key)
            pprint_diff(details["children"], indent + 2)
        elif details["type"] == "create":
            console.print(f"[green]{' ' * indent} {key}")
        elif details["type"] == "delete":
            console.print(f"[red]{' ' * indent} {key}")


def read_block(lines: list[str]) -> tuple[list[str], Block]:
    """
    Input: list of lines
    Output: tuple of (remaining_lines, block)
    """
    block = {}
    block_indent = indent(lines[0])
    while len(lines) > 0:
        [line, *lines] = lines
        # Ignore cruft
        if line.strip().startswith("!"):
            continue
        if line.strip() == "end":
            continue
        if line.strip() == "":
            continue
        # Check indent to determine block
        line_indent = indent(line)
        if line_indent == block_indent:
            # line belongs to the same block
            block[line.strip()] = {}
            continue
        if line_indent > block_indent:
            # Sub block
            if len(block) == 0:
                raise Exception(f"block without parent line: {line}")
            lines, child_block = read_block([line, *lines])
            block[list(block.keys())[-1]] = child_block
            continue
        if line_indent < block_indent:
            lines = [line, *lines]
            break
    return lines, block


@dataclass
class DeviceConfigs:
    backup: str
    rendered: str

    @cached_property
    def backup_blocks(self) -> Block:
        _, blocks = read_block(self.backup.splitlines())
        return blocks

    @cached_property
    def rendered_blocks(self) -> Block:
        _, blocks = read_block(self.rendered.splitlines())
        return blocks

    @cached_property
    def diff(self) -> Diff:
        # configs in backup; not in rendered
        return diff(self.backup_blocks, self.rendered_blocks)

    @cached_property
    def has_changes(self) -> bool:
        return len(self.diff) > 0

    def pprint_diff(self):
        pprint_diff(self.diff)


def main():
    cfg = Config.from_args()
    # Silence logging if we're printing out the device list
    global log
    log = Logger(quiet=True)

    with open(cfg.filename1) as f:
        cfg1 = f.read()
    with open(cfg.filename2) as f:
        cfg2 = f.read()

    diff = DeviceConfigs(cfg1, cfg2)
    if diff.has_changes and cfg.json:
        console.print(json.dumps({"has_changes": True, "diff": diff.diff}, indent=2))
        return
    if diff.has_changes and not cfg.json:
        console.print("[yellow]Changes detected[/]")
        print("=" * 80)
        diff.pprint_diff()
        print()
        return
    if not diff.has_changes and cfg.json:
        console.print(json.dumps({"has_changes": False}, indent=2))
        return
    if not diff.has_changes and not cfg.json:
        console.print("[green]No changes detected[/]")
        return


if __name__ == "__main__":
    main()

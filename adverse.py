#!/bin/env python3

from argparse import ArgumentParser, Namespace
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from os import chdir, getcwd, getenv
from pathlib import Path
from subprocess import CalledProcessError, run
from sys import exit, stderr
from typing import Generator, List, Optional


class ChangeDirectory(AbstractContextManager):
    def __init__(self, path: Path):
        self.path: Path = path
        self.stack: List[Path] = []

    def __enter__(self):
        self.stack.append(Path(getcwd()))
        chdir(self.path)

    def __exit__(self, *exception):
        chdir(self.stack.pop())


class ClangFormat:
    def __init__(self):
        self.path = Path(getenv("CLANG_FORMAT", "clang-format"))

    def format(self, file: Path) -> bool:
        path: Path = file.resolve()
        # Change to the parent directory of the file to make sure that the
        # appropriate .clang-format configuration file is found and used.
        with ChangeDirectory(path.parent):
            try:
                run([self.path, "-i", path.name], check=True)
            except (CalledProcessError, FileNotFoundError):
                return False
        return True


@dataclass
class GitStatus:
    path: str
    status: str

    def render(self) -> str:
        x: str = self.status[0:1]
        y: str = self.status[1:2]
        return f"{{.path = \"{self.path}\", .code = {{.x = '{x}', .y = '{y}'}}, }}"


class Git:
    def __init__(self, git: Path, repository: Path):
        self.__args = [git, "-C", repository]
        self.__root: Optional[Path] = None

    def branch(self, object_name: Optional[str] = None) -> str:
        if object_name is None:
            object_name = "HEAD"
        return self.run(["rev-parse", "--abbrev-ref", object_name])

    def commit(self, object_name: Optional[str] = None) -> str:
        if object_name is None:
            object_name = "HEAD"
        return self.run(["rev-parse", object_name])

    def dirty(self) -> bool:
        for file in self.status():
            return True
        return False

    def last_commit_time(self) -> datetime:
        iso = self.run(["log", "-1", "--format=%cd", "--date=iso-strict"])
        return datetime.fromisoformat(iso)

    def last_tagged_commit(self) -> str:
        return self.run(["rev-list", "--max-count=1", "--tags"])

    def root(self) -> Path:
        if self.__root is None:
            self.__root = Path(self.run(["rev-parse", "--show-toplevel"]))
        return self.__root

    def status(self) -> Generator[GitStatus, None, None]:
        for line in self.run(["status", "--porcelain", "-z"]).split("\x00"):
            if len(line) > 0:
                yield GitStatus(path=line[3:], status=line[0:2])

    def worktree(self) -> bool:
        return self.run(["rev-parse", "--is-inside-work-tree"]) == "true"

    def run(self, args: List[str]) -> Optional[str]:
        try:
            args = self.__args + list(args)
            result = run(args, capture_output=True, check=True, text=True)
            return result.stdout.rstrip()
        except CalledProcessError:
            return None

    def tag_name(self, object_name: Optional[str] = None) -> str:
        if object_name is None:
            object_name = "HEAD"
        return self.run(["describe", "--abbrev=0", "--tags", object_name])


def main(args: Namespace):
    git = Git(args.git, args.repository)

    if not git.worktree():
        print("error: not a git repository", file=stderr)
        return 1

    with open(args.header, "w") as f:
        branch: str = git.branch()
        commit: str = git.commit()

        f.write(
            f"#pragma once\n"
            f"\n"
            f"#include <stddef.h>\n"
            f"\n"
            f'#define GIT_BRANCH "{branch}"\n'
            f'#define GIT_COMMIT "{commit}"\n'
        )

        # Look for the latest commit that is also tagged.
        tagged_commit: str = git.last_tagged_commit()
        commit_tag: str = git.tag_name(tagged_commit)

        # The tag may be None if no tags exist, and that's fine.
        version: str = commit_tag

        if version is not None and len(version) >= 2:
            if version[0] == "v" and version[1].isdecimal():
                version = version[1:]

        # Get the time of the commit and format it as YYYYMMDD.
        commit_time: datetime = git.last_commit_time()
        commit_date: str = commit_time.strftime("%Y%m%d")

        if tagged_commit:
            if commit != tagged_commit:
                version = f"{version}-next-{commit[:7]}-{commit_date}"

        # Just use the short commit hash if no tags exist.
        if version is None:
            version = f"{commit[:7]}-{commit_date}"

        dirty_files = list(git.status())
        dirty_count = len(dirty_files)

        if dirty_count > 0:
            f.write("#define GIT_DIRTY\n")
            version = f"{version}-dirty"

        git_root: str = str(git.root())
        f.write(f'#define GIT_REPOSITORY "{git_root}"\n')

        if commit_tag is not None:
            f.write(f'#define GIT_TAG "{commit_tag}"\n')

        f.write(
            f"\n"
            f"#ifndef VERSION_STRING\n"
            f'#define VERSION_STRING "{version}"\n'
            f"#endif\n"
        )

        # Determine the length of the longest path in the list.
        max_path_length = 0
        for file in dirty_files:
            max_path_length = max(len(file.path), max_path_length)

        f.write(
            f"\n"
            f"typedef struct {{\n"
            f"\tchar branch[{len(branch) + 1}];\n"
            f"\tchar commit[{len(commit) + 1}];\n"
            f"\tstruct {{\n"
            f"\t\tsize_t count;\n"
            f"\t\t/* https://git-scm.com/docs/git-status#_output */\n"
            f"\t\tstruct {{\n"
            f"\t\t\tchar path[{max_path_length + 1}];\n"
            f"\t\t\tstruct {{\n"
            f"\t\t\t\tchar x;\n"
            f"\t\t\t\tchar y;\n"
            f"\t\t\t}} code;\n"
            f"\t\t}} files[{max(dirty_count, 1)}];\n"
            f"\t}} dirty;\n"
            f"\tchar repository[{len(git_root) + 1}];\n"
            f"}} git_status_t;\n"
            f"\n"
            f"static inline git_status_t\n"
            f"git_status(void)\n"
            f"{{\n"
            f"\treturn (git_status_t){{\n"
            f"\t\t.branch = GIT_BRANCH,\n"
            f"\t\t.commit = GIT_COMMIT,\n"
            f"\t\t.dirty = {{\n"
            f"\t\t\t.count = {dirty_count},\n"
            f"\t\t\t.files = {{\n"
        )

        if dirty_count == 0:
            dirty_files.append(GitStatus("", "  "))

        for file in dirty_files:
            f.write(f"\t\t\t\t{file.render()},\n")

        f.write("\t\t\t},\n"
                "\t\t},\n"
                "\t\t.repository = GIT_REPOSITORY,\n"
                "\t};\n"
                "}\n"
                "\n"
                "\n")

    if args.clang_format:
        cf = ClangFormat()
        cf.format(args.header)

    return 0


if __name__ == "__main__":
    ap = ArgumentParser(description="Simple C version header generator")
    ap.add_argument(
        "-F",
        "--no-clang-format",
        action="store_false",
        default=True,
        dest="clang_format",
        help="turn off clang-format formatting",
    )
    ap.add_argument(
        "-c",
        default=Path.cwd(),
        dest="repository",
        help="path to git repository",
        type=Path,
    )
    ap.add_argument(
        "-g",
        default="git",
        dest="git",
        help="path to git executable",
        type=Path,
    )
    ap.add_argument(
        "-o",
        default="version.h",
        dest="header",
        help="path to target header file",
        type=Path,
    )
    exit(main(ap.parse_args()))

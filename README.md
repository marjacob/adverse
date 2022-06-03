adverse
=======

*adverse* is a simple Git version header generator for C/C++ projects. It depends only on the Python standard library (and `git`) and is implemented as a single file. Thus, it should be farly simple to add this project as a Git submodule of your own project.

Features
--------

Version headers generated with *adverse* can provide the following information.

* `GIT_BRANCH` is the name of the current Git branch.
* `GIT_COMMIT` is the full commit hash of the latest Git commit.
* `GIT_DIRTY` exists if there are uncommitted changes to the repository.

Usage
-----

The `Makefile` provides the following targets.

* `make all` (default) alias for `make print`.
* `make clean` remove all generated files.
* `make print` generate a version header, build a test program that uses it and execute the program.
* `make test` generate a version header, then build a test program that uses it.
* `make version.h` generate a version header.

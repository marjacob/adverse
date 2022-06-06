adverse
=======

*adverse* is a simple Git version header generator for C/C++ projects. It
depends only on the Python standard library (and `git`) and is implemented as a
single file. Thus, it should be farly simple to add this project as a Git
submodule of your own project.

Features
--------

Version headers generated with *adverse* can provide the following information.

* `GIT_BRANCH` is the name of the current Git branch.
* `GIT_COMMIT` is the full commit hash of the latest Git commit.
* `GIT_DIRTY` exists if there are uncommitted changes to the repository.
* `GIT_REPOSITORY` is the full path to the current Git repository.
* `GIT_TAG` is the name of the latest Git tag, if it exists.
* `VERSION_STRING` is a version string based on commit, date and tag.

The `VERSION_STRING` may look like any of the following examples.

* `1.0.0`
* `1.0.0-dirty`
* `1.0.0-next-394f973-20220605`
* `1.0.0-next-394f973-20220605-dirty`
* `394f973-20220605`
* `394f973-20220605-dirty`

The `dirty` suffix is attached to the string if uncommitted changes exist in the
repository, whereas the `next` infix is present if commits were added after the
last tagged commit. If there are no version tags in the repository, only the
short commit hash of the most recent commit is used.

Usage
-----

The `Makefile` provides the following targets.

* `make all` (default) alias for `make print`.
* `make clean` remove all generated files.
* `make init` configure git hooks.
* `make print` generate a version header, build a test program that uses it and
  execute the program.
* `make test` generate a version header, then build a test program that uses it.
* `make version.h` generate a version header.

To ensure that the version header is always up-to-date, use a Git post-commit
hook like [this](.githooks/post-commit). Make sure that the script is executable
and that `core.hooksPath` is set correctly.

```shell
git config core.hooksPath .githooks
```

The `init` target in the `Makefile` will do the same thing.

Example
-------

Here is a complete example of a header file produced by *adverse* for its own
repository. Take a look at [test.c](test.c) for a usage example.

```c
#pragma once

#include <stddef.h>

#define GIT_BRANCH "master"
#define GIT_COMMIT "394f973b13a8e345234e5a2b97093232681719cc"
#define GIT_DIRTY
#define GIT_REPOSITORY "/home/marjacob/src/adverse"
#define GIT_TAG "v1.0.0"

#ifndef VERSION_STRING
#define VERSION_STRING "1.0.0-next-394f973-20220605-dirty"
#endif

typedef struct {
	char branch[7];
	char commit[41];
	struct {
		size_t count;
		/* https://git-scm.com/docs/git-status#_output */
		struct {
			char path[10];
			struct {
				char x;
				char y;
			} code;
		} files[2];
	} dirty;
	char repository[22];
} git_status_t;

static inline git_status_t
git_status(void)
{
	return (git_status_t){
	    .branch = GIT_BRANCH,
	    .commit = GIT_COMMIT,
	    .dirty =
	        {
	            .count = 2,
	            .files =
	                {
	                    {
	                        .path = "README.md",
	                        .code = {.x = ' ', .y = 'M'},
	                    },
	                    {
	                        .path = ".idea/",
	                        .code = {.x = '?', .y = '?'},
	                    },
	                },
	        },
	    .repository = GIT_REPOSITORY,
	};
}
```

#include "version.h"

#include <stdio.h>
#include <stdlib.h>

int
main(void)
{
	const git_status_t git = git_status();

	printf(
	    "branch: %s\n"
	    "commit: %s\n"
	    "repository: %s\n"
	    "version: %s\n",
	    git.branch,
	    git.commit,
	    git.repository,
	    VERSION_STRING);

#ifdef GIT_DIRTY
	printf("dirty:\n");

	for (size_t i = 0; i < git.dirty.count; ++i) {
		printf("  - %s\n", git.dirty.files[i].path);
	}
#endif

	return EXIT_SUCCESS;
}

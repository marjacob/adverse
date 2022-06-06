adverse := adverse.py
header  := version.h
test    := test

.PHONY: all
all: print

.PHONY: clean
clean:
	$(RM) $(header) $(test)

.PHONY: init
init:
	git config core.hooksPath .githooks/

.PHONY: print
print: $(test)
	./$(test)

$(header): $(adverse)
	./$(adverse) -o $@

$(test): test.c $(header)
	$(CC) -Wall -Wextra -Wpedantic -o2 -s -std=c11 -o $@ $<

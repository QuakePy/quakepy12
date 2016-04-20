# Makefile for QuakePy test/

.PHONY: default all check testclean clean install

default: all

all:

check: testclean
	python ./QPUnitTest.py -v

clean:

# remove all directories that have been created by tests
# these start with the string 'results'
testclean:
	rm -rf results*

install:
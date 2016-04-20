## top-level Makefile for QuakePy

SHELL=/bin/bash

SUBDIRS = test

TARGET ?= all

.PHONY: default all $(SUBDIRS) install check clean testclean

default: all

all: $(SUBDIRS)

$(SUBDIRS):
	@cd $@; $(MAKE) all

install:
	@for dir in $(SUBDIRS); do \
		pushd $$dir; $(MAKE) install; popd; \
	done

check:
	@for dir in $(SUBDIRS); do \
		pushd $$dir; $(MAKE) check; popd; \
	done

clean:
	@for dir in $(SUBDIRS); do \
		cd $$dir; $(MAKE) clean; cd $(PWD); \
	done

testclean:
	@for dir in $(SUBDIRS); do \
		cd $$dir; $(MAKE) testclean; cd $(PWD); \
	done

#! /usr/bin/make

help:
	@echo ''
	@echo 'Usage: make [command]'
	@echo ''
	@echo 'Commands:'
	@echo ''
	@echo '  lint      Lint protofiles'
	@echo ''

lint:
	@docker run --rm -v `pwd`:`pwd` -w `pwd` bufbuild/buf:1.0.0-rc8 lint

.PHONY: lint

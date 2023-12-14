#! /usr/bin/make

# Protoc command
PROTOC	?= docker run --rm -v `pwd`:`pwd` -w `pwd` namely/protoc:1.34_0

# Compiled protobuf files output
PROTO_OUT	:= pkg/proto

# Home directory for proto definitions
PROTO_HOME	:= isp-shared/proto

help:
	@echo ''
	@echo 'Usage: make [command]'
	@echo ''
	@echo 'Commands:'
	@echo ''
	@echo '  proto      Compile necessary protobuf files'
	@echo ''

proto:
	@echo "Generating proto files..."
	@mkdir -p pkg/proto
	@$(PROTOC) -I $(PROTO_HOME) \
		--go_out=paths=source_relative,plugins=grpc:$(PROTO_OUT) \
		services/docscaler/v1/docscaler.proto

test:
	@go test -count=1 `go list ./... | grep -v -e cmd`

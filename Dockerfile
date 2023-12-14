# Build proto
FROM namely/protoc:1.51_2 as protobuild

WORKDIR /src

RUN DEBIAN_FRONTEND=noninteractive apt -yq install \
    make

ENV PROTOC "protoc -I /opt/include"

COPY Makefile ./
COPY isp-shared ./isp-shared

RUN mkdir -p pkg/proto && make proto

# Build binaries
FROM golang:alpine AS build

WORKDIR /src

COPY ./go.mod ./go.sum ./

# Shared libs has to be added before go mod operations
COPY ./isp-shared ./isp-shared

# Force dns resolver to be cgo
RUN GODEBUG=netdns=cgo go mod download -x

COPY . .

COPY --from=protobuild /src/pkg/proto pkg/proto
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /docscaler-server ./cmd/server/main.go

# Final image with pre-installed docscaler
FROM python:3.9.18-bullseye AS docscaler_build

ENV PYTHONPATH="${PYTHONPATH}:/docscaler_core/deps:/docscaler_core"

# For caching purposes we're copying only requirements file here
COPY ./docscaler_core/requirements.txt /docscaler_core/requirements.txt
RUN cd docscaler_core && \
    pip install --upgrade pip && \
    pip install --target=./deps -r requirements.txt && \
    rm -rf ~/.cache/pip

# Copy the whole app
COPY ./docscaler_core /docscaler_core

RUN ln -s /docscaler_core/docscaler /usr/bin/docscaler

COPY --from=build /docscaler-server /usr/bin/docscaler-server

ENTRYPOINT ["/usr/bin/docscaler-server"]

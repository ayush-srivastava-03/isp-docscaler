module isp

go 1.14

replace isp/auth => ./auth

replace isp/config => ./config

replace isp/dialer => ./dialer

replace isp/ispsqs => ./ispsqs

replace isp/log => ./log

replace isp/profiler => ./profiler

replace isp/s3util => ./s3util

replace isp/jstream => ./jstream

replace isp/clickhouse => ./clickhouse

replace isp/bundlehistory => ./bundlehistory

replace isp/deployment => ./deployment

require (
	github.com/ClickHouse/clickhouse-go v1.5.4
	github.com/aws/aws-sdk-go v1.44.26
	github.com/google/go-cmp v0.5.8 // indirect
	github.com/imdario/mergo v0.3.13
	github.com/joho/godotenv v1.4.0
	github.com/klauspost/compress v1.15.5 // indirect
	github.com/mailru/dbr v1.1.1-0.20210811072718-e47aff06af5b
	github.com/nats-io/nats-server/v2 v2.8.4 // indirect
	github.com/nats-io/nats.go v1.16.0
	go.uber.org/zap v1.21.0
	google.golang.org/grpc v1.47.0
)

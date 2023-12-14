package jstream

import (
	"fmt"
	"isp/config"
	"time"

	"github.com/imdario/mergo"
	"github.com/nats-io/nats.go"
)

// Bundle upload/removed S3 event helper

var NATS_S3_EVENT = config.Get("NATS_S3_EVENT", "S3_BUNDLE_EVENT")

// Tunables
// For simplicity of ENV we don't expose following settings
// As they won't be changing often
var (
	s3StreamName = "minio_s3"
	maxMsgAge    = time.Hour * 24 * 7
	maxAckWait   = time.Minute * 15
)

func (p *JStream) CreateS3EventListener(name string, cb PollerHandler, opts ...*PollerSubscribeOptions) error {
	settings := &PollerSubscribeOptions{
		JobsCount:      1,
		JobErrorJitter: 5 * time.Second,
		JobMaxRetry:    25,
	}

	if len(opts) > 0 {
		mergo.Merge(opts[0], settings)
		settings = opts[0]
	}

	if _, err := p.registerStream(&nats.StreamConfig{
		Name:      s3StreamName,
		Subjects:  []string{NATS_S3_EVENT},
		Retention: nats.InterestPolicy,
		MaxAge:    maxMsgAge,
		// MaxConsumers: -1,
		// MaxMsgs:      -1,
		Discard: nats.DiscardOld,
		// MaxMsgSize:   -1,
		Storage: nats.FileStorage,
	}); err != nil {
		return fmt.Errorf("register %s stream: %v", s3StreamName, err)
	}

	if _, err := p.registerConsumer(s3StreamName, &nats.ConsumerConfig{
		Durable:       name,
		AckPolicy:     nats.AckExplicitPolicy,
		AckWait:       maxAckWait,
		DeliverPolicy: nats.DeliverNewPolicy,
		MaxDeliver:    settings.JobMaxRetry,
	}); err != nil {
		return fmt.Errorf("register consumer %s for %s stream: %v", name, s3StreamName, err)
	}

	if err := p.Subscribe(s3StreamName, name, cb, settings); err != nil {
		return fmt.Errorf("subscribe to consumer %s > %s : %v", s3StreamName, name, err)
	}

	return nil
}

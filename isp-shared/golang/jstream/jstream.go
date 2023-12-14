package jstream

import (
	"fmt"
	"sync"
	"time"

	"isp/config"
	"isp/log"

	"github.com/imdario/mergo"
	"github.com/nats-io/nats.go"
)

var (
	NATS_URI = config.Get("NATS_URI", nats.DefaultURL)
)

type PollerHandler func(msg []byte) error

type JStream struct {
	nats *nats.Conn

	subs []*nats.Subscription
	opts *JStreamOptions

	js nats.JetStreamContext
}

type JStreamOptions struct {
	// Custom NATS server URL.
	// Default is taken from NATS_SERVER env
	NatsUrl string
}

type PollerSubscribeOptions struct {
	// JobsCount specifies amount of parallel polling jobs to run. Default: 1
	JobsCount int

	// JobErrorJitter sets the delay before return (NAK) of erroneously
	// processed job back to the stream. Default: 60s
	JobErrorJitter time.Duration

	// JobMaxRetry specifies amount of attempts to process message before
	// removal from the stream. use -1 for inifinite retries. Default: 3
	JobMaxRetry int
}

func Connect(opts ...JStreamOptions) (*JStream, error) {
	var err error

	p := JStream{
		opts: &JStreamOptions{
			NatsUrl: NATS_URI,
		},
		subs: []*nats.Subscription{},
	}

	if len(opts) > 0 {
		mergo.Merge(&opts[0], p.opts)
		p.opts = &opts[0]
	}

	if err = p.connect(); err != nil {
		return nil, err
	}

	if p.js, err = p.nats.JetStream(); err != nil {
		return nil, err
	}

	return &p, nil
}

func ConnectWithRetry(opts ...JStreamOptions) (*JStream, error) {
	var c *JStream
	var err error
	for i := 0; i < 10; i++ {
		c, err = Connect()
		if err == nil {
			break
		}

		log.Msg.Infof("Unable to connect to NATS: %v. Retrying...", err)
		time.Sleep(5 * time.Second)
	}
	if c == nil {
		return nil, fmt.Errorf("Failed to connect to NATS")
	}

	return c, nil
}

func (p *JStream) Subscribe(stream string, consumer string, cb PollerHandler, opts ...*PollerSubscribeOptions) error {
	settings := &PollerSubscribeOptions{
		JobsCount:      1,
		JobErrorJitter: 60 * time.Second,
		JobMaxRetry:    3,
	}

	if len(opts) > 0 {
		mergo.Merge(opts[0], settings)
		settings = opts[0]
	}

	if settings.JobsCount <= 0 || settings.JobsCount > 30 {
		return fmt.Errorf("opts.JobsCount should be in range 1..30")
	}

	js, err := p.nats.JetStream()
	if err != nil {
		return fmt.Errorf("jetstream: %v", err)
	}

	// We use consumer name as subscription name
	// stream -> consumer -> subscription (last two names are identical)
	sub, err := js.PullSubscribe("", consumer,
		nats.Bind(stream, consumer),
	)
	if err != nil {
		return fmt.Errorf("subscribe: %v", err)
	}

	p.subs = append(p.subs, sub)

	// Run separate goroutine for consumers
	go p.processor(sub, settings, cb)

	return nil
}

func (p *JStream) Publish(subject string, msg []byte) error {
	if _, err := p.js.Publish(subject, msg); err != nil {
		return err
	}

	return nil
}

func (p *JStream) Close() {
	for _, s := range p.subs {
		if err := s.Drain(); err != nil {
			log.Msg.Errorf("drain subscription [%s:%s]: %v", s.Queue, s.Subject, err)
		}
	}
	p.nats.Close()
}

func (p *JStream) connect() error {
	var err error

	if p.nats, err = nats.Connect(p.opts.NatsUrl,
		nats.MaxReconnects(-1),
		nats.DisconnectErrHandler(func(_ *nats.Conn, e error) {
			log.Msg.Infof("Disconnected from NATS: %v", e)
		}),
		nats.ReconnectHandler(func(*nats.Conn) {
			log.Msg.Infof("Restored NATS connection")
		}),
	); err != nil {
		return err
	}

	return nil
}

func (p *JStream) processor(sub *nats.Subscription, c *PollerSubscribeOptions, cb PollerHandler) {
	for {
		msgs, err := sub.Fetch(c.JobsCount)
		if err != nil || len(msgs) == 0 {
			// Problems with receiving messages is not a disaster
			continue
		}

		// Here we run a callback per each received message in a separate goroutine.
		// Job's main loop is locked until all callbacks are done
		var wg sync.WaitGroup
		wg.Add(len(msgs))
		for i, m := range msgs {
			go func(m *nats.Msg, wg *sync.WaitGroup, i int) {
				if err := cb(m.Data); err != nil {
					log.Msg.Error(err)
					m.NakWithDelay(c.JobErrorJitter)
				} else {
					m.AckSync()
				}
				wg.Done()
			}(m, &wg, i)
		}
		wg.Wait()
	}
}

func (p *JStream) registerStream(cfg *nats.StreamConfig) (*nats.StreamInfo, error) {
	if _, err := p.js.StreamInfo(cfg.Name); err == nats.ErrStreamNotFound {
		return p.js.AddStream(cfg)
	}

	// TODO: Probably, bad idea to update always
	return p.js.UpdateStream(cfg)
}

func (p *JStream) registerConsumer(stream string, cfg *nats.ConsumerConfig) (*nats.ConsumerInfo, error) {
	if _, err := p.js.ConsumerInfo(stream, cfg.Durable); err == nats.ErrConsumerNotFound {
		return p.js.AddConsumer(stream, cfg)
	}

	// TODO: Probably, bad idea to update always
	return p.js.UpdateConsumer(stream, cfg)
}

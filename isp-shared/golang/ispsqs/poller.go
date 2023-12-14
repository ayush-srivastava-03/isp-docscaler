package ispsqs

import (
	"context"
	"fmt"
	"sync"
	"time"

	"isp/log"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/sqs"
)

// SQS Poller
// Provides a ready to use poll mechanism, which fires a callback function
// when new message is present in queue.
// Poller can have multiple jobs running to speed up polling
// for large amount messages in a queue (see setings.JobsCount).
// Each callback is fired as a separate goroutine: be aware - messages
// are processed by callback in parallel fashion
type Poller struct {
	cb         Handler
	ctx        context.Context
	cancelFunc context.CancelFunc
	region     string
	url        string
	svc        *sqs.SQS
	settings   PollerSettings
}

// Various tunables for poller.
// Those have default values, but can be overrided at the
// moment of poller creation
type PollerSettings struct {
	// How many parallel polling jobs to run
	JobsCount int

	// How many seconds to wait before returning message back to sqs.
	// Make sure that your callback function estimated work time is less than
	// ProcessingTimeout
	ProcessingTimeout int64

	// How many seconds to wait for message to arrive before return
	// empty list of messages (long polling)
	WaitMessageTimeout int64

	// Maximum number of messages to receive before firing callbacks
	MaxNumberOfMessages int64
}

// Callback function for received message from queue
type Handler func(*sqs.Message) error

func CreatePoller(ctx context.Context, region string, url string, cb Handler,
	settings ...PollerSettings) (*Poller, error) {

	sess, err := session.NewSession(&aws.Config{
		Region: aws.String(region),
	})
	if err != nil {
		return nil, fmt.Errorf("create aws session: %v", err)
	}

	c, cancelFunc := context.WithCancel(ctx)

	p := Poller{
		cb:         cb,
		ctx:        c,
		cancelFunc: cancelFunc,
		region:     region,
		url:        url,
		svc:        sqs.New(sess),
		settings: PollerSettings{
			JobsCount:           10,
			ProcessingTimeout:   30,
			WaitMessageTimeout:  20,
			MaxNumberOfMessages: 10,
		},
	}

	// Some of the default settings are overrided?
	if len(settings) > 0 {
		s := settings[0]

		if s.JobsCount > 0 {
			p.settings.JobsCount = s.JobsCount
		}

		if s.ProcessingTimeout > 0 {
			p.settings.ProcessingTimeout = s.ProcessingTimeout
		}

		if s.WaitMessageTimeout > 0 {
			if s.WaitMessageTimeout > 20 {
				return nil, fmt.Errorf("WaitMessageTimeout should be in range 1..20")
			}

			p.settings.WaitMessageTimeout = s.WaitMessageTimeout
		}

		if s.MaxNumberOfMessages > 0 {
			if s.MaxNumberOfMessages > 10 {
				return nil, fmt.Errorf("MaxNumberOfMessages should be in range 1..10")
			}

			p.settings.MaxNumberOfMessages = s.MaxNumberOfMessages
		}
	}

	return &p, nil
}

func (p *Poller) Start() {
	log.Msg.Infof("Starting sqs poller for %s (%d jobs x %d messages)",
		p.url, p.settings.JobsCount, p.settings.MaxNumberOfMessages)
	for id := 1; id <= p.settings.JobsCount; id++ {
		go p.job(id)
	}
}

// Note: we start job ids from 1
func (p *Poller) job(id int) {
	// Simple trick to distribute jobs in time:
	// Start job loop after a small delay (in settings.WaitMessageTimeout range)
	delta := p.settings.WaitMessageTimeout * int64(id-1) * 1000 / int64(p.settings.JobsCount)
	time.Sleep(time.Millisecond * time.Duration(delta))

	errorCount := 0
	for {
		msgs, err := p.pollSqs()
		if err != nil {
			// TODO: temporary workaround, to avoid spamming by requests,
			// which instantly produce errors
			if errorCount < 12 {
				errorCount++
			}
			pause := time.Second * 5 * time.Duration(errorCount)

			// Typically all jobs produce same error.
			// Display it only for first job
			if id == 1 {
				log.Msg.Errorf("%s: %v (sleeping for %v)", p.url, err, pause)
			}

			time.Sleep(pause)
			continue
		}

		errorCount = 0

		if len(msgs) == 0 {
			continue
		}

		log.Msg.Debugf("%s [job %d]: %d new messages", p.url, id, len(msgs))

		wrapper := func(m *sqs.Message, wg *sync.WaitGroup) {
			defer wg.Done()

			if err := p.cb(m); err != nil {
				log.Msg.Errorf("%s [job %d]: sqs callback error: %v", p.url, id, err)

				// Return failed message back to the queue
				if err := p.returnSqsMessage(m); err != nil {
					log.Msg.Errorf("%s [job %d]: return message to queue: %v", p.url, id, err)
				}

				return
			}

			if err := p.removeSqsMessage(m); err != nil {
				log.Msg.Errorf("%s [job %d]: remove sqs message: %v", p.url, id, err)
			}
		}

		// Here we run a callback per each received message in a separate goroutine.
		// Job's main loop is locked until all callbacks are done
		var wg sync.WaitGroup
		wg.Add(len(msgs))

		for _, message := range msgs {
			go wrapper(message, &wg)
		}

		wg.Wait()
	}
}

// Remove message from SQS
func (p *Poller) removeSqsMessage(msg *sqs.Message) error {
	_, err := p.svc.DeleteMessage(&sqs.DeleteMessageInput{
		QueueUrl:      aws.String(p.url),
		ReceiptHandle: msg.ReceiptHandle,
	})

	return err
}

// Return message back to SQS
func (p *Poller) returnSqsMessage(msg *sqs.Message) error {
	_, err := p.svc.ChangeMessageVisibility(&sqs.ChangeMessageVisibilityInput{
		QueueUrl:          aws.String(p.url),
		ReceiptHandle:     msg.ReceiptHandle,
		VisibilityTimeout: aws.Int64(0),
	})

	return err
}

// Get messages from SQS
func (p *Poller) pollSqs() ([]*sqs.Message, error) {
	result, err := p.svc.ReceiveMessage(&sqs.ReceiveMessageInput{
		AttributeNames: []*string{
			aws.String(sqs.MessageSystemAttributeNameSentTimestamp),
		},
		MessageAttributeNames: []*string{
			aws.String(sqs.QueueAttributeNameAll),
		},
		QueueUrl:            aws.String(p.url),
		MaxNumberOfMessages: aws.Int64(p.settings.MaxNumberOfMessages),
		VisibilityTimeout:   aws.Int64(p.settings.ProcessingTimeout),
		WaitTimeSeconds:     aws.Int64(p.settings.WaitMessageTimeout),
	})

	if err != nil {
		return nil, err
	}

	return result.Messages, nil
}

// TODO: We need to be able to gracefully shutdown goroutines
func (p *Poller) Stop() error {
	log.Msg.Infof("Stopping sqs poller for %s (%s)", p.url, p.region)
	p.cancelFunc()
	return nil
}

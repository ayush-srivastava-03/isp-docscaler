package ispsqs

import (
	"context"
	"testing"

	"github.com/aws/aws-sdk-go/service/sqs"
)

func TestCreatePoller(t *testing.T) {
	const (
		region = "aws-region"
		sqsurl = "http://sqs-url"
	)

	var cb = func(*sqs.Message) error {
		return nil
	}

	//
	p, err := CreatePoller(context.Background(), region, sqsurl, cb)

	if err != nil {
		t.Errorf("create poller: %v", err)
	}

	if p.region != region {
		t.Errorf("create poller: region doesn't match: %s != %s", region, p.region)
	}

	if p.url != sqsurl {
		t.Errorf("create poller: url doesn't match: %s != %s", sqsurl, p.url)
	}

	//
	p, err = CreatePoller(context.Background(), region, sqsurl, cb, PollerSettings{
		WaitMessageTimeout: 36,
	})

	if err == nil {
		t.Error("should error for invalid WaitMessageTimeout value")
	}

	//
	advancedSettings := PollerSettings{
		JobsCount:          5,
		ProcessingTimeout:  10,
		WaitMessageTimeout: 20,
	}
	p, err = CreatePoller(context.Background(), region, sqsurl, cb, advancedSettings)

	if err != nil {
		t.Errorf("create poller: %v", err)
	}

	if p.settings.JobsCount != advancedSettings.JobsCount {
		t.Errorf("create poller: JobsCount doesn't match: %d != %d", advancedSettings.JobsCount,
			p.settings.JobsCount)
	}

	if p.settings.ProcessingTimeout != advancedSettings.ProcessingTimeout {
		t.Errorf("create poller: ProcessingTimeout doesn't match: %d != %d",
			advancedSettings.ProcessingTimeout, p.settings.ProcessingTimeout)
	}

	if p.settings.WaitMessageTimeout != advancedSettings.WaitMessageTimeout {
		t.Errorf("create poller: WaitMessageTimeout doesn't match: %d != %d",
			advancedSettings.WaitMessageTimeout, p.settings.WaitMessageTimeout)
	}

	//
	p, err = CreatePoller(context.Background(), region, sqsurl, cb, PollerSettings{
		MaxNumberOfMessages: 36,
	})

	if err == nil {
		t.Error("should error for invalid MaxNumberOfMessages value")
	}
}

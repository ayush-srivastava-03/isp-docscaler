package s3util

import (
	"encoding/json"
	"fmt"
	"net/url"
	"strings"
	"time"

	"isp/log"
)

type FileS3Event int

const (
	FileAdded FileS3Event = iota
	FileRemoved

	FileUnknown
)

type FileS3 struct {
	Bucket   string
	Key      string
	SenderIP string
	Size     uint64

	Event FileS3Event
	Meta  map[string]string
}

// We're going to extract only properties we interested in
type s3Event struct {
	Records []struct {
		AWSRegion string    `json:"awsRegion"`
		Event     string    `json:"eventName"`
		Timestamp time.Time `json:"eventTime"`

		S3 struct {
			Bucket struct {
				Name string `json:"name"`
			} `json:"bucket"`
			Object struct {
				Key  string            `json:"key"`
				Size uint64            `json:"size"`
				Meta map[string]string `json:"userMetadata"`
			} `json:"object"`
		} `json:"s3"`

		Source struct {
			Host string `json:"host"`
		} `json:"source"`
	} `json:"Records"`
}

func ParseS3FileEvent(msg []byte) (*FileS3, error) {
	var event s3Event
	if err := json.Unmarshal(msg, &event); err != nil {
		return nil, fmt.Errorf("unmarshal s3 event: %v", err)
	}

	if len(event.Records) == 0 {
		return nil, fmt.Errorf("invalid format of S3 event: %s", string(msg))
	}

	data := event.Records[0]

	ev := FileUnknown
	if strings.Contains(data.Event, "ObjectCreated:") {
		ev = FileAdded
	}
	if strings.Contains(data.Event, "ObjectRemoved:") {
		ev = FileRemoved
	}

	return &FileS3{
		Event:    ev,
		Bucket:   data.S3.Bucket.Name,
		Key:      NormalizeFilePath(data.S3.Object.Key),
		SenderIP: data.Source.Host,
		Size:     data.S3.Object.Size,
		Meta:     data.S3.Object.Meta,
	}, nil
}

// Unescape URL encoded path to file
func NormalizeFilePath(path string) string {
	res, err := url.QueryUnescape(path)
	if err != nil {
		log.Msg.Errorf("normalize bundle path: %v", err)
		return path
	}

	return res
}

package s3util

import (
	"isp/config"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
)

var (
	S3_REGION = config.Get("S3_REGION")

	S3_ACCESS_KEY = config.Get("S3_ACCESS_KEY", "")
	S3_SECRET_KEY = config.Get("S3_SECRET_KEY", "")

	S3_ENDPOINT    = config.Get("S3_ENDPOINT", "")
	S3_DISABLE_SSL = config.GetBool("S3_DISABLE_SSL", false)

	S3_FORCE_PATH_STYLE = config.GetBool("S3_FORCE_PATH_STYLE", false)
)

type Session struct {
	*session.Session
}

// NewSession is a helper function to get S3 session depending on environment
// settings of service
func NewSession() *Session {
	cfg := &aws.Config{
		Region: aws.String(S3_REGION),
	}

	if S3_ACCESS_KEY != "" || S3_SECRET_KEY != "" {
		cfg.Credentials = credentials.NewStaticCredentials(S3_ACCESS_KEY, S3_SECRET_KEY, "")
	}

	if S3_ENDPOINT != "" {
		cfg.Endpoint = aws.String(S3_ENDPOINT)
	}

	if S3_DISABLE_SSL {
		cfg.DisableSSL = aws.Bool(true)
	}

	if S3_FORCE_PATH_STYLE {
		cfg.S3ForcePathStyle = aws.Bool(true)
	}

	return &Session{
		session.New(cfg),
	}
}

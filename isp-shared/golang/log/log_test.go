package log

import "testing"

func CreateLogger(t *testing.T) {
	t.Error(createLogger())
}

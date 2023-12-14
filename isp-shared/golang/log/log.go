package log

import (
	"go.uber.org/zap"
)

var Msg *zap.SugaredLogger

func init() {
	if err := createLogger(); err != nil {
		panic(err)
	}
}

func createLogger() error {
	instance, err := zap.NewDevelopment()
	if err != nil {
		return err
	}

	Msg = instance.Sugar()

	return nil
}

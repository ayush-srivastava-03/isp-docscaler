package main

import (
	"os"
	"os/signal"
	"syscall"

	"isp/log"
)

func main() {
	log.Msg.Info("Server is running")

	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGTERM)
	<-ch
}

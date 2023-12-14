package dialer

import (
	"fmt"
	"sync"

	"isp/log"

	"google.golang.org/grpc"
)

type connections struct {
	sync.Mutex
	cache map[string]*grpc.ClientConn
}

var c connections

func init() {
	c = connections{
		cache: make(map[string]*grpc.ClientConn),
	}
}

func GetClientConn(addr string, opts ...grpc.DialOption) (*grpc.ClientConn, error) {
	if c.cache[addr] != nil {
		return c.cache[addr], nil
	}

	if len(opts) == 0 {
		opts = []grpc.DialOption{
			grpc.WithInsecure(),
		}
	}

	log.Msg.Infof("Dialing %s...", addr)

	c.Lock()
	defer c.Unlock()

	var err error
	if c.cache[addr], err = grpc.Dial(addr, opts...); err != nil {
		return nil, fmt.Errorf("failed to dial service %s: %v", addr, err)
	}

	return c.cache[addr], nil
}

func Close(addr string) error {
	if c.cache[addr] != nil {
		if err := c.cache[addr].Close(); err != nil {
			return err
		}
	}

	c.Lock()
	defer c.Unlock()

	c.cache[addr] = nil

	return nil
}

func CloseAll() {
	for n := range c.cache {
		if err := Close(n); err != nil {
			log.Msg.Errorf("Error closing %s: %v", n, err)
		}
	}
}

package profiler

import (
	"isp/log"
	"runtime"
	"time"
)

type Profiler struct {
	CPUs      int
	MaxMemory uint64
	delay     time.Duration
}

func Create(delay time.Duration) Profiler {
	var x runtime.MemStats
	runtime.ReadMemStats(&x)

	return Profiler{
		CPUs:      runtime.NumCPU(),
		MaxMemory: x.Alloc,
		delay:     delay,
	}
}

func (p *Profiler) update() {
	var x runtime.MemStats
	runtime.ReadMemStats(&x)

	if x.Alloc > p.MaxMemory {
		log.Msg.Infof("[profiler] Memory consumption maxed: %.2fM", float64(x.Alloc)/1024/1024)
		p.MaxMemory = x.Alloc
	}
}

func (p *Profiler) Start() {
	for {
		p.update()
		time.Sleep(p.delay)
	}
}

package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"time"
)

var (
	apiRoot     = flag.String("apiRoot", "https://hypothes.is/api", "API root for creating test annotation")
	apiToken    = flag.String("apiToken", "", "API token for creating test annotation (env var: CHECKREALTIME_API_TOKEN")
	apiUser     = flag.String("apiUser", "", "API user (e.g. 'acct:foo@example.com') for creating test annotation (env var: CHECKREALTIME_API_TOKEN)")
	wsEndpoint  = flag.String("wsEndpoint", "wss://hypothes.is/ws", "WebSocket endpoint")
	wsOrigin    = flag.String("wsOrigin", "https://hypothes.is", "Origin header to send to websocket")
	warnLatency = flag.Duration("warnLatency", 500*time.Millisecond, "warn latency")
	critLatency = flag.Duration("critLatency", 2*time.Second, "critical latency")
	timeout     = flag.Duration("timeout", 10*time.Second, "critical latency")
)

func chk(err error, msg string) {
	if err != nil {
		log.Fatalf("error: "+msg+" (%v)\n", err)
	}
}

func chkAll(errs []error, msg string) {
	if errs != nil {
		log.Fatalf("error: "+msg+" %v\n", errs)
	}
}

func fetchFromEnv(val *string, envvar string) bool {
	envVal := os.Getenv(envvar)
	if envVal == "" {
		return false
	}
	*val = envVal
	return true
}

func nagiosCheckOutput(success bool, latency time.Duration) {
	status := "OK: received test notification in %s"
	rc := 0

	if success {
		if latency > *warnLatency {
			status = "WARN: test notification took %s to arrive"
			rc = 1
		}
		if latency > *critLatency {
			status = "CRITICAL: test notification took %s to arrive"
			rc = 2
		}
	} else {
		status = "CRITICAL: timed out waiting for test notification (%s)"
		rc = 2
	}

	fmt.Printf(status+"\n", latency)
	os.Exit(rc)
}

func main() {
	flag.Parse()

	if *apiToken == "" && !fetchFromEnv(apiToken, "CHECKREALTIME_API_TOKEN") {
		log.Fatalln("error: no API token provided")
	}
	if *apiUser == "" && !fetchFromEnv(apiUser, "CHECKREALTIME_API_USER") {
		log.Fatalln("error: no API user provided")
	}

	ws, err := wsConnect(*wsEndpoint, *wsOrigin)
	chk(err, "couldn't connect websocket")

	id, errs := createAnnotation(*apiRoot, *apiUser, *apiToken)
	chkAll(errs, "failed to create test annotation")

	start := time.Now()
	log.Printf("created test annotation (id=%v) at %v\n", id, start)

	done := make(chan time.Time)

	go func() {
		t, err := wsAwaitNotification(ws, id)
		chk(err, "failure while awaiting notification")
		done <- t
	}()

	success := false
	var latency time.Duration

	select {
	case t := <-done:
		success = true
		latency = t.Sub(start)
		log.Printf("received notification at %v (waited %v)\n", t, latency)
	case <-time.After(*timeout):
		success = false
		latency = *timeout
		log.Fatalf("timed out waiting for notification (waited %v)", *timeout)
	}

	errs = deleteAnnotation(*apiRoot, *apiUser, *apiToken, id)
	chkAll(errs, fmt.Sprintf("failed to delete annotation (id=%v)", id))

	log.Printf("deleted test annotation (id=%v)\n", id)

	err = ws.Close()
	chk(err, "couldn't close websocket")

	nagiosCheckOutput(success, latency)
}

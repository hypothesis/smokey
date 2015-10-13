package main

import (
	"fmt"
	"log"
	"os"
	"time"
)

var (
	API_ROOT    = os.Getenv("CHECKREALTIME_API_ROOT")
	API_TOKEN   = os.Getenv("CHECKREALTIME_API_TOKEN")
	API_USER    = os.Getenv("CHECKREALTIME_API_USER")
	WS_ENDPOINT = os.Getenv("CHECKREALTIME_WS_ENDPOINT")
	WS_ORIGIN   = os.Getenv("CHECKREALTIME_WS_ORIGIN")
	TIMEOUT     = 10 * time.Second
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

func main() {
	if API_TOKEN == "" {
		log.Fatalln("no API token provided: please set CHECKREALTIME_API_TOKEN")
	}
	if API_USER == "" {
		log.Fatalln("no API user provided: please set CHECKREALTIME_API_USER")
	}
	if API_ROOT == "" {
		API_ROOT = "https://hypothes.is/api"
	}
	if WS_ENDPOINT == "" {
		WS_ENDPOINT = "wss://hypothes.is/ws"
	}
	if WS_ORIGIN == "" {
		WS_ORIGIN = "https://hypothes.is"
	}

	ws, err := wsConnect(WS_ENDPOINT, WS_ORIGIN)
	chk(err, "couldn't connect websocket")

	id, errs := createAnnotation(API_ROOT, API_USER, API_TOKEN)
	chkAll(errs, "failed to create test annotation")

	start := time.Now()
	log.Printf("created test annotation (id=%v) at %v\n", id, start)

	done := make(chan time.Time)

	go func() {
		t, err := wsAwaitNotification(ws, id)
		chk(err, "failure while awaiting notification")
		done <- t
	}()

	select {
	case t := <-done:
		log.Printf("received notification at %v (waited %v)\n", t, t.Sub(start))
	case <-time.After(TIMEOUT):
		log.Fatalf("timed out waiting for notification (waited %v)", TIMEOUT)
	}

	errs = deleteAnnotation(API_ROOT, API_USER, API_TOKEN, id)
	chkAll(errs, fmt.Sprintf("failed to delete annotation (id=%v)", id))

	log.Printf("deleted test annotation (id=%v)\n", id)

	err = ws.Close()
	chk(err, "couldn't close websocket")
}

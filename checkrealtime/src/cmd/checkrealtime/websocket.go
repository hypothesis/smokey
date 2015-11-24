package main

import (
	"crypto/tls"
	"log"
	"time"

	"golang.org/x/net/websocket"
)

// wsConnect connects to the websocket and sends the setup messages (variously a
// client_id message and a catch-all filter message).
func wsConnect(endpoint, origin string) (*websocket.Conn, error) {
	config, err := websocket.NewConfig(endpoint, origin)
	if err != nil {
		return nil, err
	}

	config.TlsConfig = &tls.Config{InsecureSkipVerify: true}

	ws, err := websocket.DialConfig(config)
	if err != nil {
		return nil, err
	}

	err = websocket.JSON.Send(ws, newClientIdMessage())
	if err != nil {
		return nil, err
	}

	err = websocket.JSON.Send(ws, newFilterMessage())
	if err != nil {
		return nil, err
	}

	return ws, nil
}

// wsAwaitNotification reads each message from the passed *websocket.Conn
// object, and looks for an annotation notification.
func wsAwaitNotification(ws *websocket.Conn, id string) (time.Time, error) {
	for {
		var data map[string]interface{}
		err := websocket.JSON.Receive(ws, &data)
		if err != nil {
			return time.Time{}, err
		}
		if isMatch(data, id) {
			return time.Now(), nil
		}
	}
}

// isMatch checks if the data in a message from the websocket is an annotation
// notification matching the passed id. This is sadly quite laborious due to the
// weird format of the annotation notification message.
func isMatch(data map[string]interface{}, id string) bool {
	typ, ok := data["type"]
	if !ok {
		return false
	}
	if typ != "annotation-notification" {
		return false
	}
	payload, ok := data["payload"]
	if !ok {
		log.Println("warn: saw annotation-notification lacking payload")
		return false
	}
	annotations, ok := payload.([]interface{})
	if !ok {
		log.Println("warn: saw annotation-notification with bad payload format")
		return false
	}
	for _, annotationVal := range annotations {
		annotation, ok := annotationVal.(map[string]interface{})
		if !ok {
			log.Println("warn: saw annotation with bad format")
			return false
		}
		candidateIdVal, ok := annotation["id"]
		if !ok {
			log.Println("warn: saw annotation without an id")
			return false
		}
		candidateId, ok := candidateIdVal.(string)
		if !ok {
			log.Println("warn: saw annotation with a non-string id")
			return false
		}
		if candidateId == id {
			return true
		}
	}
	return false
}

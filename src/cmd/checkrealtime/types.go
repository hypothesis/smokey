package main

import "code.google.com/p/go-uuid/uuid"

type ClientIdMessage struct {
	MessageType string `json:"messageType"`
	Value       string `json:"value"`
}

type FilterMessageFilterActions struct {
	Create bool `json:"create"`
	Update bool `json:"update"`
	Delete bool `json:"delete"`
}

type FilterMessageFilter struct {
	MatchPolicy string                     `json:"match_policy"`
	Clauses     []string                   `json:"clauses"`
	Actions     FilterMessageFilterActions `json:"actions"`
}

type FilterMessage struct {
	Filter FilterMessageFilter `json:"filter"`
}

func newClientIdMessage() *ClientIdMessage {
	return &ClientIdMessage{
		MessageType: "client_id",
		Value:       uuid.NewRandom().String(),
	}
}

func newFilterMessage() *FilterMessage {
	return &FilterMessage{
		Filter: FilterMessageFilter{
			MatchPolicy: "include_all",
			Clauses:     []string{},
			Actions: FilterMessageFilterActions{
				Create: true,
				Update: true,
				Delete: true,
			},
		},
	}
}

package main

import (
	"encoding/json"
	"fmt"

	"github.com/parnurzeal/gorequest"
)

// createAnnotation creates a small test annotation in the API identified by the
// passed API root, and returns the id of the annotation created.
func createAnnotation(root, user, token string) (id string, errs []error) {
	request := gorequest.New()
	resp, body, errs := request.Post(root+"/annotations").
		// TLSClientConfig(&tls.Config{InsecureSkipVerify: true}).
		// SetDebug(true).
		Set("Authorization", "Bearer "+token).
		Send(fmt.Sprintf(`{
			"smokey": true,
			"permissions": {
				"read": ["group:__world__"],
				"delete": ["%s"]
			}
		}`, user)).
		EndBytes()

	if errs != nil {
		return "", errs
	}

	if resp.StatusCode != 200 {
		return "", []error{fmt.Errorf("got status %v", resp.Status)}
	}

	var annotation map[string]interface{}
	err := json.Unmarshal(body, &annotation)
	if err != nil {
		return "", []error{err}
	}

	val, ok := annotation["id"]
	if !ok {
		return "", []error{fmt.Errorf("returned annotation had no id")}
	}
	id, ok = val.(string)
	if !ok {
		return "", []error{fmt.Errorf("returned annotation had non-string id")}
	}

	return id, nil
}

// deleteAnnotation deletes the annotation identified by the passed id in the
// API identified by the passed API root.
func deleteAnnotation(root, user, token, id string) []error {
	request := gorequest.New()
	resp, _, errs := request.Delete(root+"/annotations/"+id).
		// TLSClientConfig(&tls.Config{InsecureSkipVerify: true}).
		// SetDebug(true).
		Set("Authorization", "Bearer "+token).
		End()

	if errs != nil {
		return errs
	}

	if resp.StatusCode != 200 {
		return []error{fmt.Errorf("got status %v", resp.Status)}
	}

	return nil
}

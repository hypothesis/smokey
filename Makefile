# The URL of the API endpoint
API_ENDPOINT ?= https://hypothes.is/api

.deps: requirements.txt
	pip install -r requirements.txt
	touch .deps

api-tests: .deps
	behave -D api_endpoint=${API_ENDPOINT} features/api

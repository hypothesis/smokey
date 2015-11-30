Feature: API search
  Scenario: Using the search API
    When I search with no query
    Then I should get at least 20 annotations

  Scenario: Search for annotations with a tag
    When I search for annotations tagged "hypothesis"
    Then I should get annotations tagged "hypothesis"

  Scenario: Searching for annotations by author
    When I search for annotations authored by "hypothesistest"
    Then I should get annotations authored by "hypothesistest"

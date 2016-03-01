Feature: Real-time websocket streaming
  Scenario: Receiving recently-created annotations over the websocket
    Given I am acting as the test user "smokey"
    And I am connected to the websocket
    And I request to be notified of all annotation events
    When I create a test annotation
    Then I should receive notification of my test annotation on the websocket

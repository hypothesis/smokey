Feature: Real-time websocket streaming
  Scenario: Receiving recently-created annotations over the websocket
    Given I am acting as the test user "smokey"
    And I am listening for notifications on the websocket
    When I create a test annotation
    Then I should receive a websocket notification within 30s

Feature: Via proxy
  @sauce @autoretry
  Scenario Outline: Visiting a URL through Via
    Given I am using supported browser "<browser>"
    When I visit "http://example.com" with Via
    Then I should see the Hypothesis sidebar
    And I should see at least 2 annotations

    Examples:
      | browser       |
      | Sauce-Firefox |
      | Sauce-Chrome  |
      | Sauce-Edge    |
      | Sauce-Safari  |

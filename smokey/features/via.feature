Feature: Via proxy
  Scenario: Visiting a URL through Via
    Given I am using a supported browser
      |browser|
      |Sauce-Firefox|
      |Sauce-Chrome|
    When I visit "http://example.com" with Via
    Then I should see the Hypothesis sidebar
    And I should see at least 2 annotations

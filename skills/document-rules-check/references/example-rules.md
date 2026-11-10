# Example rules

The web application's default rules, ready to use as `rules.json`:

```json
{
  "rules": [
    {
      "id": "R1",
      "title": "No performance figures",
      "text": "The document must not contain any numeric value that reveals the performance of the system, such as range, speed, accuracy, capacity, endurance or power.",
      "examples": ["The maximum detection range is 50 km."],
      "non_examples": ["Document version 2.1, issued in March 2024."]
    },
    {
      "id": "R2",
      "title": "No personal names",
      "text": "The document must not mention the names of individual people."
    },
    {
      "id": "R3",
      "title": "No exact locations",
      "text": "The document must not disclose exact geographic locations, coordinates or site names where the system is deployed or tested."
    }
  ]
}
```

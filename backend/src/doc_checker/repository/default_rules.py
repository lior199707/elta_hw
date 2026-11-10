from __future__ import annotations

# (title, text) pairs inserted on first start so a fresh install can run a check immediately.
DEFAULT_RULES: tuple[tuple[str, str], ...] = (
    (
        "No performance figures",
        "The document must not contain any numeric value that reveals the performance of the "
        "system, such as range, speed, accuracy, capacity, endurance or power.",
    ),
    (
        "No personal names",
        "The document must not mention the names of individual people.",
    ),
    (
        "No exact locations",
        "The document must not disclose exact geographic locations, coordinates or site names "
        "where the system is deployed or tested.",
    ),
)

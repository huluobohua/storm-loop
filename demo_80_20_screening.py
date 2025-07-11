"""Demonstration of the PRISMA 80/20 screening assistant."""

from knowledge_storm.prisma_assistant import PRISMAScreener


if __name__ == "__main__":
    screener = PRISMAScreener()
    records = [
        "Randomized controlled trial of new therapy shows positive results",
        "Study protocol for upcoming clinical trial",
        "Editorial commentary on research methods",
    ]
    for rec in records:
        result = screener.screen(rec)
        reasons = ", ".join(result.reasons)
        print(
            f"{rec}\n  -> {result.decision}"
            f" (confidence {result.confidence:.2f})"
            f" - {reasons}"
        )

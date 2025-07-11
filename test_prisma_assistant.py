from knowledge_storm.prisma_assistant import PRISMAScreener


def test_screen_include():
    screener = PRISMAScreener(threshold=0.4)
    text = "Randomized controlled trial evaluating outcomes"
    result = screener.screen(text)
    assert result.decision == "include"
    assert result.confidence >= 0.4


def test_screen_exclude():
    screener = PRISMAScreener(threshold=0.4)
    text = "Protocol for an upcoming trial"
    result = screener.screen(text)
    assert result.decision == "exclude"


def test_batch_screen():
    screener = PRISMAScreener(threshold=0.4)
    records = [
        "Randomized trial results",
        "Editorial commentary"
    ]
    decisions = [r.decision for r in screener.batch_screen(records)]
    assert decisions == ["include", "exclude"]

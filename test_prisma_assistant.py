from knowledge_storm.prisma_assistant import PRISMAScreener


def test_screen_include():
    screener = PRISMAScreener(threshold=0.4)
    text = "Randomized controlled trial evaluating outcomes"
    result = screener.screen(text)
    assert result.decision == "include"
    assert result.confidence == 0.6


def test_screen_exclude():
    screener = PRISMAScreener(threshold=0.4)
    text = "Protocol for an upcoming trial"
    result = screener.screen(text)
    assert result.decision == "exclude"
    assert result.confidence == 0.2


def test_screen_unsure():
    screener = PRISMAScreener(threshold=0.4)
    text = "Preliminary findings"
    result = screener.screen(text)
    assert result.decision == "unsure"
    assert result.confidence == 0.0


def test_conflict_resolution():
    screener = PRISMAScreener(threshold=0.4)
    text = "Randomized trial protocol commentary"
    result = screener.screen(text)
    assert result.decision == "exclude"
    assert result.confidence == 0.4


def test_batch_screen():
    screener = PRISMAScreener(threshold=0.4)
    records = [
        "Randomized trial results",
        "Editorial commentary"
    ]
    decisions = [r.decision for r in screener.batch_screen(records)]
    assert decisions == ["include", "exclude"]

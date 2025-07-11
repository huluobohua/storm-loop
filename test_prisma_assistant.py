from knowledge_storm.prisma_assistant import PRISMAScreener


def test_screen_include():
    screener = PRISMAScreener(threshold=0.5)
    text = "Randomized controlled trial evaluating outcomes"
    result = screener.screen(text)
    assert result.decision == "include"
    assert result.confidence == 0.6


def test_screen_exclude():
    screener = PRISMAScreener(threshold=0.8)
    text = "Protocol editorial commentary letter case report"
    result = screener.screen(text)
    assert result.decision == "exclude"
    assert result.confidence == 1.0


def test_screen_unsure():
    screener = PRISMAScreener()
    text = "Randomized trial results"
    result = screener.screen(text)
    assert result.decision == "unsure"
    assert result.confidence == 0.6


def test_conflict_resolution():
    screener = PRISMAScreener()
    text = "Randomized trial protocol"
    result = screener.screen(text)
    assert result.decision == "exclude"
    assert result.confidence == 0.2


def test_batch_screen():
    screener = PRISMAScreener(threshold=0.5)
    records = [
        "Randomized trial results",
        "Editorial commentary case report",
    ]
    decisions = [r.decision for r in screener.batch_screen(records)]
    assert decisions == ["include", "exclude"]

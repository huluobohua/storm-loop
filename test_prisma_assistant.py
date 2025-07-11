from knowledge_storm.prisma_assistant import PRISMAScreener


def test_screen_include():
    screener = PRISMAScreener(threshold=0.4)
    text = "Randomized controlled trial evaluating outcomes"
    result = screener.screen(text)
    assert result.decision == "include"
    assert result.confidence == 0.6


def test_screen_exclude():
    screener = PRISMAScreener(threshold=0.4)
    text = "Protocol editorial commentary"
    result = screener.screen(text)
    assert result.decision == "exclude"
    assert result.confidence == 0.6


def test_screen_conflict_include():
    screener = PRISMAScreener(threshold=0.8)
    text = "Randomized study protocol"
    result = screener.screen(text)
    assert result.decision == "include"
    assert result.confidence == 0.4


def test_screen_tie_unsure():
    screener = PRISMAScreener(include_patterns=["apple"], exclude_patterns=["orange"], threshold=0.8)
    result = screener.screen("apple orange")
    assert result.decision == "unsure"
    assert result.confidence == 1.0


def test_screen_unsure():
    screener = PRISMAScreener()
    result = screener.screen("Preliminary data")
    assert result.decision == "unsure"
    assert result.confidence == 0.0


def test_batch_screen():
    screener = PRISMAScreener(threshold=0.4)
    records = [
        "Randomized trial results",
        "Editorial commentary"
    ]
    decisions = [r.decision for r in screener.batch_screen(records)]
    assert decisions == ["include", "exclude"]


def test_empty_patterns_and_text():
    screener = PRISMAScreener(include_patterns=[], exclude_patterns=[], threshold=0.8)
    result = screener.screen("")
    assert result.decision == "unsure"
    assert result.confidence == 0.0


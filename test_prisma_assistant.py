from knowledge_storm.prisma_assistant import PRISMAScreener


def test_screen_include_exact_confidence():
    screener = PRISMAScreener(threshold=0.4)
    text = "Randomized controlled trial evaluating outcomes"
    result = screener.screen(text)
    assert result.decision == "include"
    assert result.confidence == 0.6


def test_screen_exclude_exact_confidence():
    screener = PRISMAScreener(threshold=0.4)
    text = "Case report with editorial commentary"
    result = screener.screen(text)
    assert result.decision == "exclude"
    assert result.confidence == 0.6


def test_screen_unsure():
    screener = PRISMAScreener(threshold=0.4)
    text = "Novel approach to teaching methods"
    result = screener.screen(text)
    assert result.decision == "unsure"
    assert result.confidence == 0.0


def test_conflict_include_overrides():
    screener = PRISMAScreener(threshold=0.3)
    text = "Randomized trial protocol"
    result = screener.screen(text)
    assert result.decision == "include"
    assert result.confidence == 0.4


def test_conflict_exclude_overrides():
    screener = PRISMAScreener(threshold=0.3)
    text = "Protocol commentary randomized"
    result = screener.screen(text)
    assert result.decision == "exclude"
    assert result.confidence == 0.4

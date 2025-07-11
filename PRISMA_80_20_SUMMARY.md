# PRISMA Assistant 80/20 Screening System

This module provides a lightweight implementation of an automated screening
assistant inspired by the PRISMA guidelines. The goal is to rapidly exclude
clearly irrelevant sources and include highly relevant ones with approximately
80% confidence.

## Overview

`PRISMAScreener` uses inclusion and exclusion keyword patterns. For each record
the number of hits is converted to a score (hits divided by total patterns).
When a score meets the configured threshold (default `0.8`) **and** exceeds the
opposing score, the record is automatically included or excluded. If both types
of keywords appear but the threshold is not reached, the screener defaults to
exclusion. Otherwise the decision is marked as `unsure`.

The `ScreeningResult` dataclass captures the decision, confidence and reasoning
used for each record. Batched screening is supported via `batch_screen`.

This implementation is deliberately simple to demonstrate the 80/20 workflow. In
practice the patterns and scoring logic can be extended with additional signals
or machine learning models.

# PRISMA Assistant 80/20 Screening System

This module provides a lightweight implementation of an automated screening
assistant inspired by the PRISMA guidelines. The goal is to rapidly exclude
clearly irrelevant sources and include highly relevant ones with approximately
80% confidence.

## Overview

`PRISMAScreener` uses inclusion and exclusion keyword patterns. For each record
the number of keyword hits is converted into simple scores. When a score
exceeds the configured threshold (default `0.8`) and is greater than the
opposite score, the record is automatically included or excluded. If neither
score meets the threshold, the side with more keyword hits is chosen; if they
are equal the decision is `unsure`.

The `ScreeningResult` dataclass captures the decision, confidence and reasoning
used for each record. Batched screening is supported via `batch_screen`.

`PRISMAScreener` guards against division by zero when no patterns are provided
and validates the threshold value.

This implementation is deliberately simple to demonstrate the 80/20 workflow. In
practice the patterns and scoring logic can be extended with additional signals
or machine learning models.

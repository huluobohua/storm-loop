# PRISMA Assistant 80/20 Screening System

This module provides a lightweight implementation of an automated screening
assistant inspired by the PRISMA guidelines. The goal is to rapidly exclude
clearly irrelevant sources and include highly relevant ones with approximately
80% confidence.

## Overview

`PRISMAScreener` uses a set of inclusion and exclusion keyword patterns. For
each record, the number of keyword hits is converted into simple scores. If the
inclusion or exclusion score exceeds the configured threshold (default `0.8`)
and is greater than the opposite score, the record is automatically included or
excluded. Otherwise the decision is marked as `unsure`.

The `ScreeningResult` dataclass captures the decision, confidence and reasoning
used for each record. Batched screening is supported via `batch_screen`.

This implementation is deliberately simple to demonstrate the 80/20 workflow. In
practice the patterns and scoring logic can be extended with additional signals
or machine learning models.

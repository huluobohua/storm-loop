# PRISMA Assistant 80/20 Screening System

This module provides a lightweight implementation of an automated screening
assistant inspired by the PRISMA guidelines. The goal is to rapidly exclude
clearly irrelevant sources and include highly relevant ones with approximately
80% confidence.

## Overview

`PRISMAScreener` counts keyword hits for inclusion and exclusion patterns.
Scores are calculated as the fraction of hits relative to the number of
patterns. A record is included or excluded when the respective score meets or
exceeds the configured threshold (default `0.8`) **and** is greater than the
opposite score. If exclusion keywords outnumber inclusion keywords the record is
excluded even when scores fall below the threshold. In all other cases the
decision is marked as `unsure`.

The `ScreeningResult` dataclass captures the decision, confidence and reasoning
used for each record. Batched screening is supported via `batch_screen`.

This implementation is deliberately simple to demonstrate the 80/20 workflow. In
practice the patterns and scoring logic can be extended with additional signals
or machine learning models.

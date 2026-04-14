# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenReview-py is the official Python client library for the [OpenReview](https://openreview.net) scientific review platform. It provides API clients, venue/conference/journal management tools, and workflow automation for academic peer review.

## Common Commands

### Installation (development)
```bash
pip install -e .
```

### Running tests
Use the test-runner agent to execute tests.

Tests use pytest with pytest-selenium (Firefox/geckodriver). The geckodriver binary must be at `tests/drivers/geckodriver`.

### Documentation
```bash
pip install -e ".[docs]"
cd docs && make html
```

## Architecture

### Dual API Client System
The library maintains two API clients for backward compatibility:
- **V1 Client** (`openreview.Client` in `openreview/openreview.py`): Legacy client connecting to port 3000
- **V2 Client** (`openreview.api.OpenReviewClient` in `openreview/api/client.py`): Modern client connecting to port 3001

Both expose similar domain objects (Note, Invitation, Group, Edge, Tag, Profile) but with different schemas. V2 adds Edit objects for tracking changes.

### Core Domain Models
The platform is built around an **invitation-driven workflow**:
- **Groups** define roles and permissions (authors, reviewers, area chairs, SACs)
- **Invitations** define what actions users can take and their parameters
- **Notes** represent submissions, reviews, decisions, and other content
- **Edges** represent relationships (assignments, conflicts, bids)
- **Tags** represent labels assigned to notes, groups, invitations
- **Edits** (V2 only) track all modifications to notes, invitations, and groups

### Venue Management Modules
- `openreview/venue/` — Generic venue framework (`Venue` class), invitation builder, group builder, matching
- `openreview/conference/` — Legacy conference management (`Conference` class)
- `openreview/journal/` — Journal workflow management
- `openreview/arr/` — ACL Rolling Review specific logic
- `openreview/stages/` — Reusable workflow stages (submission, review, meta-review, decision, etc.)
- `openreview/workflows/` — Workflow templates

### Support Modules
- `openreview/tools.py` — Utility functions for venue management, matching, profile operations
- `openreview/profile/management.py` — Profile-related invitation setup (DBLP, arXiv, ORCID integration)
- `openreview/llm/` — LLM integration via litellm

### Test Infrastructure
- `tests/conftest.py` — Shared fixtures: `client` (V1), `openreview_client` (V2), `helpers` (user creation, queue management, UI interaction)
- `Helpers.create_user()` — Creates and activates test users
- `Helpers.await_queue()` / `Helpers.await_queue_edit()` — Waits for async server-side job processing
- Tests are large integration tests that exercise the full stack including both API servers

## CI/CD

- CircleCI runs tests across Python 3.9–3.13 with Docker services (MongoDB, Redis, Elasticsearch)
- PR builds detect modified test files and run only those
- Full test suite is parallelized across 10 containers split by timing
- Published to PyPI from master branch

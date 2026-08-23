"""
Source adapters. One module per box in the SOURCES row of the architecture.

Three of the five sources do not live in GitHub. Rather than pretend they do,
each adapter reports its own availability, and every metric derived from a
missing source resolves to "insufficient evidence" instead of a number. A
blank is honest; a zero is a lie.
"""
from .base import SourceStatus, Availability
from . import github, board, deploys, incidents

__all__ = ["SourceStatus", "Availability", "github", "board", "deploys", "incidents"]

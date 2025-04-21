"""
Integration test: fetch and print the most recent truth social post.
Requires valid TRUTH_USERNAME and TRUTH_PASSWORD in .env.
Run with pytest -s to see output.
"""
import pytest

from trading.injestion import TruthClient


import os

@pytest.mark.skipif(
    not (os.getenv('TRUTH_USERNAME') and os.getenv('TRUTH_PASSWORD')),
    reason="Skipping live fetch: TRUTH_USERNAME and TRUTH_PASSWORD must be set in environment"
)
def test_print_latest_live():
    tc = TruthClient()
    posts = list(tc.get_new_posts())
    assert posts, "No posts fetched. Check your .env credentials and connectivity."
    latest = posts[-1]
    print(f"Latest post id: {latest.id}")
    print(f"Latest text: {latest.text}")
import os
import time

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get('DEADLINE_PROBE') != '1',
    reason='temporary CI experiment; runs only when DEADLINE_PROBE=1',
)


def test_runs_past_the_testsuite_deadline(capsys):
    for minute in range(50):
        with capsys.disabled():
            print(f'deadline probe: minute {minute}', flush=True)
        time.sleep(60)

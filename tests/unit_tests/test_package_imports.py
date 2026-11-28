import importlib

import pytest

import openreview


@pytest.mark.parametrize('name', ['agora', 'venue_request'])
def test_subpackage_is_not_replaced_by_its_inner_module(name):
    assert getattr(openreview, name) is importlib.import_module(f'openreview.{name}')
    # the names the subpackage used to export are still exported
    assert getattr(openreview, name).__all__

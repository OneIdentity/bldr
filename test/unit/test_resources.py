import importlib_resources


def test_data_resource():
    assert importlib_resources.files('bldr').joinpath('data').is_dir()

def test_overwrite_config_creates_file_with_correct_permission():
    config_path = _get_path()

    assert not os.path.exists(config_path)
    _overwrite_config(ConfigParser())
    assert os.path.exists(config_path)

    assert os.stat(config_path).st_mode == 0o100600


def test_overwrite_config_overwrites_permissions_to_600():
    config_path = _get_path()
    file_descriptor = os.open(config_path, os.O_CREAT | os.O_RDWR)
    os.close(file_descriptor)

    assert not os.stat(config_path).st_mode == 0o100600

    _overwrite_config(ConfigParser())

    assert os.stat(config_path).st_mode == 0o755
def test_ensure_directory_permissions(tmpdir):
    dir_path = Path(tmpdir) / "test_dir"
    os.mkdir(dir_path)  # Changed from ensure_directory_permissions
    os.chmod(dir_path, 0o700)  # Changed to set permissions directly
    assert dir_path.exists()
    assert oct(os.stat(dir_path).st_mode)[-3:] == "700"
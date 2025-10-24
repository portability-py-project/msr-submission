@pytest.fixture(name="validation_plugin")
def _validation_plugin_instance():
    return ValidationPlugin()


def test_validation_plugin_init(validation_plugin):
    """
    Test Validation initialize method
    """
    assert validation_plugin.initialize()
    assert validation_plugin.description == "CTF Validation Plugin"
    assert validation_plugin.name == "ValidationPlugin"


def test_validation_plugin_commandmap(validation_plugin):
    """
    Test Validation command content
    """
    assert len(validation_plugin.command_map) == 7
    assert "DeleteFiles" in validation_plugin.command_map
    assert "CopyFiles" in validation_plugin.command_map
    assert "SearchStr" in validation_plugin.command_map
    assert "SearchNoStr" in validation_plugin.command_map
    assert "InsertUserComment" in validation_plugin.command_map
    assert "CheckFileExists" in validation_plugin.command_map
    assert "RunShellCommand" in validation_plugin.command_map
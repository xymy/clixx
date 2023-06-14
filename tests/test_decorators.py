import clixx


def test_docstrings() -> None:
    assert clixx.argument.__doc__ == clixx.Argument.__doc__
    assert clixx.option.__doc__ == clixx.Option.__doc__
    assert clixx.flag_option.__doc__ == clixx.FlagOption.__doc__
    assert clixx.append_option.__doc__ == clixx.AppendOption.__doc__
    assert clixx.count_option.__doc__ == clixx.CountOption.__doc__
    assert clixx.help_option.__doc__ == clixx.HelpOption.__doc__
    assert clixx.version_option.__doc__ == clixx.VersionOption.__doc__
    assert clixx.argument_group.__doc__ == clixx.ArgumentGroup.__doc__
    assert clixx.option_group.__doc__ == clixx.OptionGroup.__doc__

from repo2career.reports.archify import split_command


def test_split_command_uses_posix_rules_on_linux_and_macos() -> None:
    command = "archify --input '/tmp/project input.json' --output '/tmp/report.svg'"
    expected = [
        "archify",
        "--input",
        "/tmp/project input.json",
        "--output",
        "/tmp/report.svg",
    ]
    assert split_command(command, platform="posix") == expected


def test_split_command_preserves_windows_paths_without_wrapper_quotes() -> None:
    command = '"C:\\Program Files\\Archify\\archify.exe" --input "D:\\Project Data\\input.json"'
    assert split_command(command, platform="nt") == [
        "C:\\Program Files\\Archify\\archify.exe",
        "--input",
        "D:\\Project Data\\input.json",
    ]

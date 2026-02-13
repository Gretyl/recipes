from {{cookiecutter.package_name}}.main import hello_world


def test_hello_world_returns_greeting() -> None:
    assert hello_world() == "Hello, world!"

from bishop.tools.registry import ToolRegistry, ToolSpec


def test_registry_registers_and_calls_tool():
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="echo",
            description="Echo input.",
            parameters={"type": "object", "properties": {"text": {"type": "string"}}},
            fn=lambda text: f"echo:{text}",
        )
    )

    assert registry.call("echo", {"text": "hi"}) == "echo:hi"


def test_registry_rejects_duplicate_tool_names():
    registry = ToolRegistry()
    spec = ToolSpec(
        name="echo",
        description="Echo input.",
        parameters={"type": "object", "properties": {}},
        fn=lambda: "ok",
    )
    registry.register(spec)

    try:
        registry.register(spec)
    except ValueError as exc:
        assert "tool already registered" in str(exc)
    else:
        raise AssertionError("expected duplicate registration to fail")


def test_registry_accepts_json_string_arguments():
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="echo",
            description="Echo input.",
            parameters={"type": "object", "properties": {"text": {"type": "string"}}},
            fn=lambda text: text,
        )
    )

    assert registry.call("echo", '{"text": "hi"}') == "hi"


def test_registry_returns_error_for_unexpected_tool_arguments():
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="no_args",
            description="Returns a constant.",
            parameters={"type": "object", "properties": {}},
            fn=lambda: "ok",
        )
    )

    result = registry.call("no_args", {"unexpected": "value"})

    assert result.startswith("ERROR: invalid arguments for tool 'no_args':")


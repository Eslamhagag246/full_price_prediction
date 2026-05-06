import os
import streamlit.components.v1 as components

_COMPONENT_DIR = os.path.dirname(os.path.abspath(__file__))

_component_func = components.declare_component(
    "voice_command_component",
    path=os.path.join(_COMPONENT_DIR, "frontend", "dist")
)


def voice_command(
    label="🎙️ Voice command",
    lang="en-US",
    button_text="Start listening",
    stop_text="Stop",
    key=None,
):
    return _component_func(
        label=label,
        lang=lang,
        button_text=button_text,
        stop_text=stop_text,
        key=key,
        default=None,
    )

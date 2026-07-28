"""
Guards the REST/WS response contract — both transports are built from the
shared _build_voice_response(), so the REST schema must always be
constructible from it and the WS payload must be a superset of its fields.
"""

from app.agents.state import PipelineState
from app.api.voice import _build_voice_response
from app.schemas.schemas import VoiceQueryResponse


def test_builder_covers_every_rest_field():
    payload = _build_voice_response(PipelineState(raw_text="hi"))
    missing = set(VoiceQueryResponse.model_fields.keys()) - set(payload.keys())
    assert not missing, f"_build_voice_response is missing REST fields: {missing}"


def test_rest_response_constructible_from_builder():
    payload = _build_voice_response(
        PipelineState(
            raw_text="hi",
            response_text="hello",
            intent="order_status",
            recommended_action="Inform",
            ticket_created=True,
        )
    )
    response = VoiceQueryResponse(**payload)
    assert response.response_text == "hello"
    assert response.ticket_created is True

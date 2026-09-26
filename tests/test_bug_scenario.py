from relaygrid.models import TelemetrySample
from relaygrid.scada.state import StateStore
from relaygrid.services.telemetry_service import TelemetryService
from relaygrid.telemetry.historian import merge_live_and_recovery


def test_recovery_merge_and_retries_never_move_state_backwards():
    recovered = [TelemetrySample("P1", 10.0, 7, 110.0)]
    live = [TelemetrySample("P2", 11.0, 7, 220.0)]
    merged = merge_live_and_recovery(live, recovered)
    assert [(sample.point_id, sample.sequence) for sample in merged] == [("P1", 7), ("P2", 7)]

    telemetry = TelemetryService()
    telemetry.ingest(TelemetrySample("P1", 20.0, 2, 2.0))
    telemetry.ingest(TelemetrySample("P1", 10.0, 1, 1.0))
    assert telemetry.latest("P1").sequence == 2

    state = StateStore()
    assert state.apply("SW1", "closed", version=4)
    assert not state.apply("SW1", "open", version=4)
    assert state.discrete["SW1"] == "closed"

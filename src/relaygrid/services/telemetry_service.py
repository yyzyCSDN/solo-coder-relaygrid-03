from __future__ import annotations
from collections import defaultdict
from relaygrid.models import TelemetrySample
from relaygrid.telemetry.quality import newest_valid, stale

class TelemetryService:
    def __init__(self,max_age_s: float=120.0):
        self.max_age_s=max_age_s
        self._by_point: defaultdict[str,list[TelemetrySample]]=defaultdict(list)
    def ingest(self,sample: TelemetrySample): self._by_point[sample.point_id].append(sample)
    def latest(self,point_id: str):
        rows=self._by_point.get(point_id,[])
        if not rows: return None
        # Order within a point is by sequence (timestamp as tiebreak), not by
        # arrival time: an older backfilled sample arriving late must never
        # become the point's latest value.
        return max(rows,key=lambda s:(s.sequence,s.timestamp_s))
    def snapshot(self,now_s: float):
        out={}
        for point_id in sorted(self._by_point):
            sample=self.latest(point_id)
            out[point_id]={"value":None if sample is None else sample.value,"stale":stale(sample,now_s,self.max_age_s),"quality":None if sample is None else sample.quality}
        return out

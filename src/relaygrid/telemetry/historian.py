from __future__ import annotations
from dataclasses import dataclass, field
from relaygrid.models import TelemetrySample

@dataclass
class Cursor:
    point_id: str
    sequence: int
    timestamp_s: float

@dataclass
class Historian:
    rows: dict[str,list[TelemetrySample]]=field(default_factory=dict)

    def append(self,sample:TelemetrySample):
        bucket=self.rows.setdefault(sample.point_id,[])
        if bucket and sample.sequence<=bucket[-1].sequence: raise ValueError("historian sequence must increase")
        bucket.append(sample)

    def query(self,point_id:str,start_s:float,end_s:float):
        return [s for s in self.rows.get(point_id,[]) if start_s<=s.timestamp_s<=end_s]

    def after(self,cursor:Cursor,limit:int=1000):
        rows=[s for s in self.rows.get(cursor.point_id,[]) if s.sequence>cursor.sequence]
        return rows[:limit]

    def latest_cursor(self,point_id:str):
        rows=self.rows.get(point_id,[])
        if not rows: return Cursor(point_id,-1,float('-inf'))
        s=rows[-1]; return Cursor(point_id,s.sequence,s.timestamp_s)


def merge_live_and_recovery(live:list[TelemetrySample],recovered:list[TelemetrySample]):
    # Key on point AND sequence: equal sequence numbers at different points
    # are independent samples and must never overwrite one another.
    by_key: dict[tuple[str,int],TelemetrySample]={}
    for sample in recovered+live:
        key=(sample.point_id,sample.sequence)
        cur=by_key.get(key)
        # Newer timestamp wins; on a tie the live copy (processed later) wins,
        # so replaying the same backfill never clobbers the live value.
        if cur is None or sample.timestamp_s>=cur.timestamp_s: by_key[key]=sample
    return sorted(by_key.values(),key=lambda s:(s.sequence,s.point_id))


def detect_gaps(samples:list[TelemetrySample]):
    if not samples: return []
    ordered=sorted(samples,key=lambda s:s.sequence); gaps=[]
    for a,b in zip(ordered,ordered[1:]):
        if b.sequence>a.sequence+1: gaps.append((a.sequence+1,b.sequence-1))
    return gaps

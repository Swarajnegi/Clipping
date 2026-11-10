"""Lightweight compressed-packet metadata comparison; no decoding or media mutation."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from motion_edit import audio_packets
a=audio_packets(ROOT/'public/clips/peterson_20261108_01-small-steps/clip_01.mp4')
b=audio_packets(P/'drafts/01-small-steps.dialogue.mp4')
changes=[{'index':i,'original':x,'muxed':y} for i,(x,y) in enumerate(zip(a['packets'],b['packets'])) if x!=y]
result={'original_streams':a['streams'],'muxed_streams':b['streams'],
    'original_count':len(a['packets']),'muxed_count':len(b['packets']),'changes':changes,
    'packet_payloads_identical':[x.get('data_hash') for x in a['packets']]==[x.get('data_hash') for x in b['packets']]}
(P/'qa/audio-copy-diagnostic.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))

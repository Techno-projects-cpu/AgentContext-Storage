#!/usr/bin/env python3
"""Write a Telugu .srt from the film's timing, so the story can be followed with the sound off."""
import json
import pathlib


def stamp(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


timing = json.loads(pathlib.Path("audio/timing.json").read_text())
out = []
for i, s in enumerate(timing["segments"], 1):
    out.append(f"{i}\n{stamp(s['start'])} --> {stamp(s['end'])}\n{s['caption']}\n")
pathlib.Path("telugu-crow.te.srt").write_text("\n".join(out))
print(f"srt: {len(out)} cues")

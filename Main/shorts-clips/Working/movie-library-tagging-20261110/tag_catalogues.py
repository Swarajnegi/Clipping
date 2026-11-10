"""Promote visually grounded editorial labels into existing catalogue records."""
import collections
import re
import sys
from pathlib import Path

from evidence import W, MOVIES, ROOT, SCANS, read, save
from movie_library import CUES, inventory, semantic_cues

ALIASES = {
    "attention":"focus","aftermath":"setback","anticipation":"anticipation","calculation":"focus",
    "composure":"resolve","concern":"hesitation","consequence":"setback","consequences":"setback",
    "consideration":"reflection","cooperation":"teamwork","coordination":"teamwork","creation":"craft",
    "dialogue":"connection","distress":"pressure","effort":"resolve","escape":"pressure",
    "exhaustion":"relief","experimentation":"craft","family":"connection","fatigue":"relief",
    "honesty":"trust","industry":"craft","intimacy":"connection","investigation":"focus",
    "negotiation":"conflict","pause":"reflection","patience":"focus","planning":"focus",
    "regret":"reflection","rescue":"help","restraint":"resolve","return":"transition","risk":"pressure",
    "search":"focus","solidarity":"teamwork","stillness":"reflection","struggle":"setback",
    "suspense":"anticipation","suspicion":"hesitation","tension":"pressure","thought":"reflection",
    "unity":"teamwork","vigilance":"focus","watchfulness":"focus","work":"craft",
}
USES = {
    "anticipation":"waiting for the outcome","choice":"facing a decision","conflict":"meeting resistance",
    "connection":"finding common ground","craft":"making or refining something with care",
    "focus":"giving a task your full attention","grief":"feeling the weight of a loss",
    "help":"reaching out or accepting support","hesitation":"being unsure of the next move",
    "isolation":"carrying something alone","listening":"taking in what someone says",
    "pressure":"feeling the stakes rise","recovery":"regrouping before the next attempt",
    "reflection":"taking a moment to think","relief":"letting the tension settle",
    "repetition":"putting in the same work again","resolve":"deciding to keep going",
    "sacrifice":"accepting what a decision costs","setback":"absorbing a setback",
    "teamwork":"getting something done together","transition":"moving into a new situation",
    "trust":"letting someone in","victory":"letting a win land",
}
MOODS = {
    "anticipation":"anticipatory","conflict":"tense","connection":"human","craft":"methodical",
    "focus":"focused","grief":"somber","help":"tender","hesitation":"uncertain","isolation":"lonely",
    "listening":"attentive","pressure":"tense","recovery":"resilient","reflection":"quiet",
    "relief":"released","resolve":"determined","teamwork":"cooperative","victory":"uplifting",
}

def editorial(action, cues, mood, framing, evidence, fit=None):
    cues=list(dict.fromkeys(cues))[:4]
    assert set(cues)<=CUES.keys(), cues
    return dict(action=action,cues=cues,mood=list(dict.fromkeys(mood)),framing=framing,
                fit=fit or ("Possible use for " + " or ".join(USES[tag] for tag in cues[:2]) + "." if cues
                            else "Use as setting or texture when the exact line calls for this picture."),
                evidence=evidence)

def reuse_name(row):
    action=re.sub(r"^\d+-","",Path(row["file"]).stem).replace("-"," ")
    action=action[:1].upper()+action[1:]+"."
    tags=row["tags"]
    cues=[cue for tag in tags if tag != "vulnerability"
          for cue in sorted(semantic_cues(tag) | ({ALIASES[tag]} if tag in ALIASES else set()))]
    if not cues:
        cues=sorted(semantic_cues(action))
    framing=next((hint for pattern,hint in (
        (r"close up|profile|face|eyes","Face detail"),
        (r"hands?|gloves?|object|boots","Object or hand detail"),
        (r"wide|landscape|above|cityscape|skyline","Wide or establishing"),
        (r"silhouette|shadow","Silhouette or low light"),
        (r"two figures|two men|two people|conversation","Shared frame"),
    ) if re.search(pattern,action.lower())), "Verify crop in the intended interval")
    return editorial(action,cues,[MOODS[c] for c in cues if c in MOODS][:3],framing,
                     {"status":"prior_visual_review","detail":row["review"]})

def annotations(path):
    result={}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line or line.startswith("#"):
            continue
        ids,action,cues,mood,framing,*fit=line.split("|")
        for ident in ids.split():
            assert int(ident) not in result, (path,ident)
            result[int(ident)]=[action,cues.split(),mood.split(),framing,*fit]
    return result

def run(apply):
    pilot_rows=read(W/"pilot.json")
    notes=annotations(W/"pilot-tags.tsv")
    assert set(notes)==set(range(1,len(pilot_rows)+1))
    pilot={r["id"]:editorial(*notes[i],{"status":"excerpt_samples",
                "excerpt_seconds":r["excerpt_seconds"],"sheet":r["sheet"]})
           for i,r in enumerate(pilot_rows,1)}
    clarified={r["id"]:r for r in read(W/"clarified.json")}
    examples=read(W/"examples.json")
    example_notes=annotations(W/"examples-tags.tsv")
    assert set(example_notes)==set(range(1,len(examples)+1))
    for i,r in enumerate(examples,1):
        action,cues,mood,framing,fit=example_notes[i]
        times=r["excerpt_seconds"]
        indices=sorted({0,len(times)//3,2*len(times)//3,len(times)-1})
        pilot[r["id"]]=editorial(action,cues,mood,framing,{"status":"excerpt_samples",
                "excerpt_seconds":[times[n] for n in indices],"sheet":r["sheet"]},fit=fit)
    counts=collections.Counter()
    pending=[]
    for path in sorted(MOVIES.glob("*/catalogue.json")):
        cat=read(path)
        name=SCANS.get(path.parent.name)
        frame_records={r["candidate"]:r for r in read(W/f"{name}-evidence.json")} if name else {}
        labels=annotations(W/f"{name}-tags.tsv") if name else {}
        assert set(labels)==set(frame_records),(name,sorted(frame_records.keys()-labels.keys()),sorted(labels.keys()-frame_records.keys()))
        for row in cat["clips"]:
            ident=f"{path.parent.name}/{row['file']}"
            source=frame_records.get(row.get("candidate_id"))
            if ident in pilot:
                info=pilot[ident]
            elif source:
                action,cues,mood,framing=labels[row["candidate_id"]]
                if ident in clarified:
                    frames=clarified[ident]
                    evidence={"status":"excerpt_samples","excerpt_seconds":frames["excerpt_seconds"],
                              "sheet":frames["sheet"]}
                else:
                    status="source_frame" if source["source_second"] is not None and cues else "unresolved"
                    evidence={"status":status,"source_second":source["source_second"],
                              "scan_block":source["block"],"sheet":source["sheet"]}
                info=editorial(action,cues,mood,framing,evidence)
            else:
                info=reuse_name(row)
            row["editorial"]=info
            counts[info["evidence"]["status"]]+=1
        pending.append((path,cat))
    if apply:
        for path,cat in pending:
            save(path,cat)
        assert len(inventory(MOVIES,strict=True))==sum(counts.values())
    print(dict(counts))

if __name__=="__main__":
    run("--apply" in sys.argv)

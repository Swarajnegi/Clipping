# Movie cutaway library

Standalone, silent source-native excerpts. They remain usable after the owner removes the original pack.

For new intake, save 5–10 seconds of usable footage around the action, with
trim room where available. Short legacy excerpts can still serve quick
inserts. Put trims for individual edits in the project's `Working` folder.

| Pack | Available excerpts | Source dimensions | Intake status |
| --- | ---: | --- | --- |
| [About Time - Mary](About%20Time%20-%20Mary/CATALOGUE.md) | 8 | 1920×1080 | Initial reviewed selection |
| [Creed - Adonis Creed](Creed%20-%20Adonis%20Creed/CATALOGUE.md) | 6 | 3840×1600 | Initial reviewed selection |
| [Good Will Hunting](Good%20Will%20Hunting/CATALOGUE.md) | 19 | 3840×2060 | Initial reviewed selection |
| [The Pursuit of Happyness](The%20Pursuit%20of%20Happyness/CATALOGUE.md) | 10 | 1920×800 | Initial reviewed selection |
| [Avengers Endgame - Steve Rogers](Avengers%20Endgame%20-%20Steve%20Rogers/CATALOGUE.md) | 121 | 3840×1608 | Existing library |
| [Blade Runner 2049 - Officer K](Blade%20Runner%202049%20-%20Officer%20K/CATALOGUE.md) | 420 | 3840×1600 | Existing library |
| [Breaking Bad - Walter White S05A](Breaking%20Bad%20-%20Walter%20White%20S05A/CATALOGUE.md) | 201 | 3840×2160 | Existing library |
| [Fight Club](Fight%20Club/CATALOGUE.md) | 12 | 1920×800 | Existing library |
| [Iron Man](Iron%20Man/CATALOGUE.md) | 41 | 3840×1600 | Existing library |
| [Luke Glanton - The Place Beyond the Pines](Luke%20Glanton%20-%20The%20Place%20Beyond%20the%20Pines/CATALOGUE.md) | 74 | 3840×1600 | Existing library |
| [Peaky Blinders - Tommy Shelby S04](Peaky%20Blinders%20-%20Tommy%20Shelby%20S04/CATALOGUE.md) | 192 | 1920×1080 | Existing library |
| [Peaky Blinders - Tommy Shelby S06](Peaky%20Blinders%20-%20Tommy%20Shelby%20S06/CATALOGUE.md) | 222 | 3840×2160 | Existing library |
| [Suits - Harvey Specter](Suits%20-%20Harvey%20Specter/CATALOGUE.md) | 6 | 1920×1080 | Reviewed selection from E: pack |
| [The Wolf of Wall Street](The%20Wolf%20of%20Wall%20Street/CATALOGUE.md) | 3 | 3840×1600 | Reviewed selection from E: pack |
| [Whiplash](Whiplash/CATALOGUE.md) | 9 | 3840×1600 | Reviewed selection from E: pack |

**1,344 catalogued excerpts available on D:.** Counts were reconciled with the files on disk. Source timecodes for missing local files remain in the affected catalogues.

Search across packs by the spoken beat from the Clipping workspace:

```powershell
& '.venv/Scripts/python.exe' scripts/movie_library.py search "trying again after failure" --min-duration 5 --limit 12
& '.venv/Scripts/python.exe' scripts/movie_library.py validate
```

Each `catalogue.json` records visible action, possible dialogue cues, mood, framing
and the evidence behind those tags. Search brings up matching shots from
different films or series first. Check the chosen shot in motion at the planned
source offset before using it. The tag review and its contact sheets are in
`Working/movie-library-tagging-20261110`.

Posting reuse for the film and television footage is unresolved.

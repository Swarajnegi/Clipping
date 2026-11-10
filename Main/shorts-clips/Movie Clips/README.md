# Movie cutaway library

Standalone, silent source-native excerpts. They remain usable after the owner removes the original pack.

| Pack | Excerpts | Source dimensions | Intake status |
| --- | ---: | --- | --- |
| [Avengers Endgame - Steve Rogers](Avengers%20Endgame%20-%20Steve%20Rogers/CATALOGUE.md) | 121 | 3840×1608 | Existing library |
| [Blade Runner 2049 - Officer K](Blade%20Runner%202049%20-%20Officer%20K/CATALOGUE.md) | 420 | 3840×1600 | Verified intake |
| [Breaking Bad - Walter White S05A](Breaking%20Bad%20-%20Walter%20White%20S05A/CATALOGUE.md) | 201 | 3840×2160 | Existing library |
| [Daredevil - Matt Murdock S02](Daredevil%20-%20Matt%20Murdock%20S02/CATALOGUE.md) | 74 | 3840×2160 | Existing library |
| [Fight Club](Fight%20Club/CATALOGUE.md) | 29 | 1920×800 | Existing library |
| [Iron Man](Iron%20Man/CATALOGUE.md) | 41 | 3840×1600 | Existing library |
| [Jon Snow](Jon%20Snow/CATALOGUE.md) | 24 | 3840×2160 | Existing library |
| [Luke Glanton - The Place Beyond the Pines](Luke%20Glanton%20-%20The%20Place%20Beyond%20the%20Pines/CATALOGUE.md) | 75 | 3840×1600 | Verified intake |
| [Peaky Blinders - Tommy Shelby S04](Peaky%20Blinders%20-%20Tommy%20Shelby%20S04/CATALOGUE.md) | 192 | 1920×1080 | Existing library |
| [Peaky Blinders - Tommy Shelby S06](Peaky%20Blinders%20-%20Tommy%20Shelby%20S06/CATALOGUE.md) | 222 | 3840×2160 | Existing library |

**1399 standalone excerpts**. Catalogue and files reconciled.

Search across packs by the spoken beat from the Clipping workspace:

```powershell
& '.venv/Scripts/python.exe' scripts/movie_library.py search "trying again after failure" --min-duration 2 --limit 12
& '.venv/Scripts/python.exe' scripts/movie_library.py validate
```

Each `catalogue.json` records visible action, possible dialogue cues, mood, framing
and the evidence behind those tags. Search brings up matching shots from
different films or series first. Check the chosen shot in motion at the planned
source offset before using it. The tag review and its contact sheets are in
`Working/movie-library-tagging-20261110`.

Posting reuse for the film and television footage is unresolved.

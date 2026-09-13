# Real-game reference animations

Every batch-3 run is paired with an actual animation from a shipped game, reconstructed
from real game data — the graphics are fetched from pret decompilation repos and
assembled per the games' own frame tables and documented cadences. **No pixels were
drawn or synthesized**; only cropping, tile placement from OAM data, documented flips
and offsets, palette application, backdrop color, and 8x NEAREST upscaling. Exact
sources, hashes, frame counts, and cadence citations: [`provenance.json`](provenance.json).

| File | Real animation | Data source | Cadence |
| --- | --- | --- | --- |
| `ref-party-icon-pulse.gif` | Emerald party icon, continuous 2-frame healthy loop | pret/pokeemerald `graphics/pokemon/pikachu/icon.png` | 100 ms/frame (`pokemon_icon.c` sAnim_0) |
| `ref-textbox-arrow-bob.gif` | Emerald textbox ▼ bob, 0/+1/+2/+1 px | pret/pokeemerald `graphics/fonts/down_arrow.png` | 134 ms/step (`text.c` sDownArrowYCoords) |
| `ref-coin-spin.gif` | Pokémon TCG duel coin, full 8-step spin | pret/poketcg `coin.png` + `anims3.asm` AnimData167/FrameTable79 | 67 ms/frame (4 ticks) |
| `ref-item-get-bounce.gif` | Emerald Poké Ball open + field sparkle one-shot | pret/pokeemerald `balls/` + `field_effects/pics/sparkle.png` | 84 ms open steps (`pokeball.c`), 100 ms sparkle |
| `ref-status-flash.gif` | Emerald PSN status badge, binary alert blink | pret/pokeemerald `graphics/interface/status_icons.png` | 134 ms on/off (era binary-blink idiom) |
| `ref-ie7-new-tab-insert.gif` | IE7 new-tab insert: stub → 'Connecting...' tab → titled tab, one-frame swaps | screen recording YouTube `PC6flwPVMKg` (2008-05-28), cropped only — not game data | 15 fps native; insert 1 frame, 'Connecting...' ~0.6 s |

Skipped: `ref-card-flip.gif` — no real flip frames exist in poketcg (its card anims are
shuffle translations) and no other real source was fetchable, so none was fabricated.

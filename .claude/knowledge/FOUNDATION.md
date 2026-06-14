# FOUNDATION — provenance of the vendored base-pack docs

The seven docs below are **vendored copies** from the base **Agent Knowledge Pack**, frozen into
this bundle so it is self-contained. They *will* diverge from the base over time; this manifest
makes divergence **visible** instead of surprising, in both directions.

**Check:** `python3 scripts/foundation-check.py` verifies the vendored files against the hashes
below (drift = an uncatalogued edit). Add `--base <path-to-base-pack>` to also compare against
the base copies. After an intentional vendored edit, update the known-divergence list below and
run `--update` to refresh the hashes. Hashes are sha256 (first 16 hex) over **normalized**
content (CRLF→LF, trailing whitespace stripped) so line endings never masquerade as drift.

| Vendored doc | Role | Vendored hash (normalized) |
|---|---|---|
| `agent-body-of-knowledge.md` | The reasoning constitution | `e1b21663cf7ce324` |
| `agent-rules-of-the-road.md` | Tiers, gates, the loop | `fdb348ad1e46ba1c` |
| `agent-persona-catalog.md` | The persona roster's source | `eaed01f23beb50a4` |
| `layered-optimized-architecture.md` | LOA — AI-integrated architecture | `05fbe0cf47f89c78` |
| `engineering-governance.md` | SDLC lenses around the code | `513c4a28581dc94f` |
| `testing-strategy.md` | The proof discipline | `f8fe2b508718f43c` |
| `csharp-style-guide.md` | C# house style | `678e031151c1a84a` |

## Known intentional divergences (vendored ≠ base, by design)

| Doc | Pack-side change | Status in base pack |
|---|---|---|
| `agent-body-of-knowledge.md` | Latest-stable-SDK default policy (currently .NET 10 LTS / C# 14; previews excluded; repo pin wins) | **pending back-port** |
| `testing-strategy.md` | Stale version/example references removed; tracks the latest-SDK policy | **pending back-port** |
| `csharp-style-guide.md` | §2.6 constant-on-the-left comparisons added; §2.2 example fixed to match | **pending back-port** |

Everything else matches the base at vendoring time (engineering-governance differs only in line
endings, which normalization ignores). When the base pack absorbs a back-port, re-vendor the doc
here, clear its row above, and run `foundation-check.py --update`.

# Risk model

## What it does
Turns two rainfall numbers per district into one of four levels:
low, moderate, high, severe.

    effective_rain = peak forecast day (mm) + 0.2 × rain over past 5 days (mm)

## Where each number comes from
| Number | Value | Source |
|---|---|---|
| Level boundaries | 64.5 / 115.6 / 204.5 mm per 24h | IMD rainfall categories (heavy / very heavy / extremely heavy) |
| Antecedent factor | 0.2 | Naidu et al. 2017, Amboori (Kerala) landslide threshold |
| Antecedent window | 5 days | Same study (best-fitting window) |
| Peak day, not 2-day sum | n/a | IMD categories are defined per 24 hours |

## Known limits
- The 0.2 factor comes from one site and shallow landslides. Using it for river and backwater floods is an extrapolation.
- Forecasts come from a model grid. In Wayanad, July 2024, observed rain was reported to be about five times the forecast, so the engine can under-warn in the Ghats.
- One coordinate per district. Rainfall varies a lot inside a district.
- Open-Meteo's days run midnight to midnight; IMD's run 08:30 to 08:30.
- "Low" never means "safe". The agent must point callers to official IMD and KSDMA warnings.
- Hazard type is not part of the score. No source ranks hazards against each other.

## Validation plan
1. Backtest on 10-20 recorded events and 10-20 ordinary monsoon days; report hits, misses and false alarms.
2. Test forecast skill separately using Open-Meteo's Previous Runs API (2024 onward), starting with Wayanad, July 2024.
3. Next version: district-relative thresholds from long observed records.
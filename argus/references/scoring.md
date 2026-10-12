# Channel prioritization rubric

Score each dimension with an **integer 1–5**, using evidence where available and stated assumptions otherwise:

| Key | Meaning | Weight points |
|---|---|---:|
| `icp_fit` | How concentrated is the primary ICP here? | 5 |
| `intent` | Are people actively looking for a solution? | 4 |
| `reachability` | Can the maker genuinely engage this audience? | 3 |
| `speed` | Can the channel give a signal within weeks? | 3 |
| `cost` | 5 = cheap, 1 = expensive | 2 |
| `effort` | 5 = easy to execute, 1 = resource-heavy | 2 |
| `risk` | 5 = low moderation, reputation and policy risk, 1 = high | 1 |

Weights sum to 20 points. Result out of 100:

```
score = icp_fit*5 + intent*4 + reachability*3 + speed*3 + cost*2 + effort*2 + risk*1
```

This is the same as `round(20 * (0.25*icp_fit + 0.20*intent + 0.15*reachability + 0.15*speed + 0.10*cost + 0.10*effort + 0.05*risk))`, without floating-point rounding. Range: 20 to 100.

## Rules

- A score is a way to compare channels, not a prediction. Never present it as a statistic.
- If an input is unknown, say so and score it conservatively (3), or ask. Do not invent evidence to justify a score.
- Mark `basis` as `evidence` or `assumption` for each channel. A high score built on assumptions is a hypothesis to test.
- If a community or platform **prohibits promotion**, set `promotion_allowed: false`. The channel can stay in the table as a place to learn and help, but not to post promotional content, whatever the score.
- Validate the top two channels in weeks 1–2. Promote channel #3 only after the checkpoint. Do not run more than three at once.
- Prefer channels where the founder has real standing or can earn it by being useful. Cold reach with no standing scores low on `reachability`.

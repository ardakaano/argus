# Experiment design

Give each experiment one hypothesis, one change, one number that decides it.

## Template

- **Hypothesis**: "If [change], then [audience] will [behavior], because [reason]."
- **Channel**: where it runs.
- **Test**: smallest version that produces a real signal. Who, how many, how long.
- **KPI**: one primary metric with a clear denominator (for example, "installs → first feedback", not "engagement").
- **Decision gate**: the number that means *continue*, *change* or *stop*. Say it is a proposed threshold, not a forecast.
- **Budget ceiling**: if the user gave one. Never spend without approval.
- **Within 48h**: can it start in two days? At least one experiment must.

## Shape of a good set of five

1. **Problem proof**: do target users already feel the pain? (5 short conversations, public-thread analysis.)
2. **Message test**: which promise gets more clicks or replies? (two landing-page headlines, two hooks.)
3. **Channel test**: does the top channel produce qualified conversations? (one participation-first post or thread series.)
4. **Activation test**: do people reach the first value moment? (onboarding variant, concierge setup.)
5. **Willingness-to-pay test**: will anyone commit? (pre-order, paid pilot, price-page click-through, direct ask.)

## Sample-size honesty

Early tests have tiny samples. Treat 5–20 data points as a direction, not as proof. State what the result would and would not show. Prefer qualitative signals (who replied, what they said, what they tried to do) next to counts.

## Kill criteria

Define in advance what, after the first two weeks, means "change the ICP, the promise or the channel" or "stop". Examples:

- Fewer than 3 of 10 target conversations confirm the pain unprompted.
- Zero qualified replies from the top two channels after a fair attempt.
- Users install but none reach the first value moment, and two onboarding fixes did not change it.

Write the criteria down before running the tests. Otherwise a weak result will get explained away.

## Adapting to the stage

The set of five assumes testers exist. Adapt it, keeping five tests and at least one startable in 48 hours:

- **No product yet:** swap the activation test for a fake-door or concierge test (a landing page, a manual service). Swap willingness-to-pay for a price question in the conversations or a pre-order page.
- **No audience yet:** the channel test is one-to-one outreach to people with a real connection to the topic, or a warm introduction, not a post. Keep it personal, disclose who you are, and make saying no easy. Never bulk-message.
- **Zero budget:** every experiment costs 0 (`budget: "0"`); say so rather than inventing a spend. Suggest a small cap only as the user's own optional choice.
- **Budget in another currency:** state it in the user's currency (`budget` field in the report), never convert silently.

## Small budgets

With a small budget (for example $300 or 2000 TL), the default is **do not spend yet**. Hold the money behind a checkpoint: spend only after a free test shows signal. Never invent rate cards or prices for sponsorships and ads; if you did not verify them, say so and give the test as "ask for a quote". Split the budget into a plan (`budget_plan`): what is spent now, what is conditional on which result, and what stays in reserve.

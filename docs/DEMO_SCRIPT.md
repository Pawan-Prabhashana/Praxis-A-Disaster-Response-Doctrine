# Praxis — 5-minute demo script

The goal: land the four signature moments in order and close the loop. Every
number on screen is real or explicitly flagged.

## Before you start (once)

```bash
just db-up && just migrate && just data-load   # real public data (needs network)
just demo-seed                                 # showcase playbooks + fixed-seed stress runs
just dev                                       # api + web
```

Open **http://localhost:5173**. Select the scenario **2017 South-West Monsoon
Floods — Kalu Ganga** in the top bar. Leave the LLM off (default) — the brief and
after-action work without it.

> **If the network dies mid-demo:** the app shell and already-loaded data keep
> working offline (a service worker caches them); the status pill shows *Offline*
> and an honest "cached data" banner appears. The `/act` brief still generates
> (deterministic template). Only the CARTO basemap tiles may not render.

---

## 1 — Sense: real basin data, honestly flagged (45s)

Go to **Sense**. Say:

> "This is the real 2017 Kalu Ganga flood event. 12 affected districts, ~14.6M
> people, 3,341 recorded historical incidents, 1,659 candidate shelters — all
> from public sources: COD population, UNOSAT flood extent, OSM, GloFAS,
> DesInventar."

Point at the **SAMPLE** badges on Landslide susceptibility and Road closures.

> "Praxis never fakes certainty. Anything synthetic or assumed is flagged in the
> UI — landslide zonation is a placeholder until we ingest real NBRO data; road
> closures are a sample. Real data is marked real."

Open **Data provenance** to show the sources. *(Optional: switch language to
සිංහල / தமிழ் in the top bar — the whole interface, including honesty labels,
translates; district names stay English.)*

## 2 — Decide: build, compare, and the robustness reversal (2 min)

Go to **Decide** → **Compare**. Tick **Wide coverage** and **Focused &
resourced**.

> "Two strategies. On the deterministic scorecard, *Wide coverage* wins — 82.6
> vs 71.6. It prioritises five districts."

Now the key beat — the **stress test**. Both showcase playbooks already have a
fixed-seed Monte Carlo run, so this is reproducible.

> "But a good average hides fragility. We stress-test each strategy with a seeded
> Monte Carlo over documented uncertainty in the *parameters* — this is modeled
> (epistemic) uncertainty, not a fake weather forecast; the 2017 event is
> historical, so there's no ensemble to draw on, and we say so."

Show the **robustness reversal** callout:

> "Under uncertainty the ranking flips. *Focused & resourced* has a higher
> worst-plausible floor (p05 ~66) than *Wide coverage* (~63), even though it
> scores lower on paper. Spreading the same resources thin looks best on average
> but breaks on a bad day. **The deterministic winner is not the robust choice.**"

## 3 — Act: a trustworthy one-click brief (1 min)

Go to **Act**. Pick **Wide coverage** → **Generate brief**.

> "One click turns the chosen strategy into an operational brief a commander could
> hand to field teams — situation, tasking, expected performance, provenance."

The trust line (this is the point judges probe):

> "The narrative can be AI-structured, but **the AI never invents a number.**
> Every figure is computed by Praxis, and a numeric guard validates every number
> in the generated text against the source facts — a hallucinated figure is
> rejected and replaced by the deterministic template. With no API key it's
> fully template-generated. Then it exports to HTML and a real PDF."

Click **Download PDF**.

## 4 — Learn: the inverted alignment that closes the loop (1 min)

Go to **Learn**. Pick **Wide coverage** → the after-action is already computed.

> "Finally we close the loop: predicted vs. **recorded**. This compares the
> strategy's at-risk ranking against the *actual* recorded 2017 impact from
> DesInventar — the historical baseline, not the outcome of running our plan.
> We're explicit about that."

The payoff — point at the **INVERTED** alignment badge and the scatter:

> "The rankings are **inverted** — Spearman −0.5. Praxis ranked **Colombo** the
> #1 at-risk district by flood exposure, but Colombo recorded **zero deaths** in
> 2017. **Ratnapura**, which our flood model ranked *last*, recorded the **most
> deaths — 84** — because it's landslide country the inundation model
> under-weights."

Land it:

> "That's the loop closing. The data itself tells us the next doctrine
> improvement: weight recorded-impact history and landslide susceptibility, not
> flood exposure alone — which motivates ingesting real NBRO landslide data. Sense
> → Decide → Act → Learn, on real data, honestly."

---

## One-line pitch

> "Praxis is a disaster-response command platform for Sri Lanka that turns real
> public data into deliberate action — with transparent scoring, honest
> uncertainty, an AI brief that can't fabricate numbers, and an after-action
> review that already found a real, actionable blind spot in flood-only planning."

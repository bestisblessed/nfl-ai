# Q1: Is EV the same as my edge calculation in the original results while though?
# A1: 
No. They measure different things:
  - Edge % (in your CSV): model fair probability − book fair probability (vig removed). Unit: percentage points. Price-agnostic after de‑vig.
  - EV %: expected return per $1 at the posted odds (with vig). Uses model fair probability and the actual price.

They’re related but not equal. Example (Cam Ward):
  - Edge % = 73.8% − 52.9% = 20.9%
  - EV % at −128 = 0.738*(100/128) − (1−0.738) ≈ 31.5%

Rules of thumb:
  - Edge % tells if your model disagrees with the book’s true probability.
  - EV % tells how profitable the bet is at the current price.
  - If you priced at the book’s fair odds (vig removed), EV would be 0% when Edge % = 0, and have the same sign as Edge %.

---

# Q2: Can you explain it to me like a beginner?
# A2:
Simple Explanations:
- Edge %: How much more likely you think an outcome is than the book thinks (after removing their fee). It’s just “your fair probability − book’s fair probability.” Use it to rank bets.
- EV % (Expected Value): How much money you expect to make per $1 bet at the actual posted odds. If EV is 20%, long-term you’d make about $0.20 per $1. Use it to decide if a bet is worth taking at the current price.
- Kelly %: A sizing guide. It tells what fraction of your bankroll to bet to maximize long‑term growth given your probability and the posted odds. Most people use a small fraction of Kelly (like 1/4 Kelly) to control risk.

Example with numbers:
- Your model says a QB throws an INT 70% of the time.
- The book’s fair (vig-removed) probability is 50%.
  - Edge % = 70% − 50% = 20% (you think it happens much more often than the book).
- The posted price is −120 (you must risk $120 to win $100).
  - EV % uses your 70% and the −120 price to compute profit per $1. If EV = 15%, that means +$0.15 per $1 on average.
  - Kelly % uses the same inputs to suggest a bet size. If Kelly = 10%, many bettors would stake 2.5% (1/4 Kelly).

---

# Q3: Can you compare the differences between both versions here? Are there pros and cons of either or or do professionals always do the removed method?
# A3:
Short answer: They differ. Add-vig edges are larger by roughly the market’s total probability V (= over_prob + under_prob). Exact relationship:
  - E_fair = M − B/V
  - E_vig = M·V − B
  - E_vig = V · E_fair
  So with typical V ≈ 1.06 (≈6% vig), add‑vig edges are ~6% higher than remove‑vig edges.

Example (your files):
  - Cam Ward: Remove‑vig edge 20.9% vs Add‑vig edge 22.2% ⇒ ratio ≈ 1.061 (matches the market vig).
  - Stafford: 16.0% vs 17.0% ⇒ ratio ≈ 1.059.

Pros/cons:
  - Remove vig (normalize the book): 
    - Pros: True “fair” disagreement with the market, comparable across books/markets, best for model calibration and ranking signals.
    - Cons: Doesn’t directly reflect what you’ll pay; not the realized EV vs posted price.
  - Add vig to model (use actual market V):
    - Pros: Aligns with actual prices faced; useful for EV and stake sizing at quoted odds.
    - Cons: Inflates edges in proportion to vig; varies by book/market; less ideal for comparing model quality.

What pros do:
  - Standard: De‑vig the market to get fair book probabilities and compare to fair model probabilities (for signal quality and target “fair line”).
  - Execution: Compute EV versus the actual posted price (with vig) for bet selection and sizing.
  - In practice: Keep both views. Use remove‑vig for model/market disagreement; use actual-price EV for whether/how much to bet.

Steps: I'll add EV and Kelly to the remove-vig output by computing expected value and Kelly fraction using model fair probabilities vs posted odds, then run the comparison to verify the table and CSV include the new columns.
    1. Use your model’s fair probability p (from the remove‑vig output) and the posted book line (with vig) to compute EV and Kelly.
    2. Do not use the de‑vigged book probability for EV/Kelly; those use the actual price you face.

    Formulas (for Over side at posted American odds A):
    - Convert A to net payout per $1 stake b:
    - If A ≥ 0: b = A/100
    - If A < 0: b = 100/|A|
    - EV per $1: EV = p·b − (1 − p)
    - Kelly fraction: f = (b·p − (1 − p)) / b, then max(f, 0)

    So, from your remove‑vig table, take:
    - p = model fair probability
    - A = posted Over American odds
    Compute EV and Kelly as above.
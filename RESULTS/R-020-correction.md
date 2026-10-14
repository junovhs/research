# R-020 correction · The "uneconomic" conclusion used Euler as the comparator

**Date:** 2026-10-14 UTC. **Track: EXPLORATORY: YES; PREREGISTERED: NO; POD: NO; NOVELTY UNVERIFIED. Evidence: REPORTED** (the correction rests on the R-021 and R-022 COMPLETE archives). **Claim class: KNOWN_METHOD_BENCHMARK.**

## What R-020 concluded

R-020 measured explicit-Euler error (first order, max-norm ≈0.14·h) and concluded that a 1e-9 continuous-model certificate needs about 10⁹ steps, so the Euler-based continuous extension of R-014 is uneconomic. The measured constant is correct.

## What is wrong

The conclusion compared a certified 1e-9 target against **explicit Euler**, which no serious continuous solver uses for this accuracy. The fair comparator is a standard higher-order method: [R-021](R-021.md) measured that, for the same D=16 problem, DOP853 reaches about 1e-10 error with ≈824 evaluations, and RK4 reaches 1e-9 with ≈4096. The "10⁹ steps" figure is therefore not an economic bound on the continuous target.

## Replacement statement

For the continuous Allen–Cahn target in this family, a non-rigorous adaptive full-domain integrator reaches about 1e-9 at D=512 with ≈1.3×10⁷ scalar updates (R-022, reference not cross-checked). A continuous omission claim must beat that **and** carry a validated continuous bound. Euler is not a valid baseline.

## What is unchanged

R-020's first-order Euler constant, its archive, and its discrete-recurrence result for R-014. The R-020 record itself is append-only and is not edited; this file is the linked correction.

Linked: [R-020](R-020.md), [R-021](R-021.md) (includes the R-022 run).

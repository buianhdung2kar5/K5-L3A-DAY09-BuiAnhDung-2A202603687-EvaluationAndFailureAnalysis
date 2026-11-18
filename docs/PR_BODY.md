# Lab 9 — Evaluation & Failure Analysis (Bùi Anh Dũng, 2A202603687)

Dán nội dung này vào mô tả PR `starter/d09` → `main` (trong bản fork). Mọi output do script sinh ra ngày 2026-11-18.

## Core — gate: `fixed` exit 0, `seeded_regression` exit 1
```
$ python -m lab9.gate --pr reports/eval_fixed.json --baseline reports/baseline_v1.json
gate: PR E-fixed-20261118-acd5 vs main E-swarm-20261118-acd5 · eval set acd5dd7bdd44
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           1.0      {"min": 0.95}                                                         ok
  refund_amount_correct  1.0      {"min": 0.95, "no_significant_drop": true} Δ +0.014 CI [+0.000, +0.043] ok
  pass_rate              1.0      {"min": 0.85, "no_significant_drop": true} Δ +0.014 CI [+0.000, +0.043] ok
  pass_5                 1.0      {"min": 0.8}                                                          ok
  cost_per_success       48.7157  {"max_increase": 0.1}                                                 ok
  reply_matches_ledger   1.0      {"min": 1.0}                                                          ok
  proposal_matches_quote 1.0      {"min": 0.95}                                                         ok
exit 0 — merge

$ python -m lab9.gate --pr reports/eval_seeded_regression.json --baseline reports/baseline_v1.json
gate: PR E-seeded_regression-20261118-acd5 vs main E-swarm-20261118-acd5 · eval set acd5dd7bdd44
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           0.9286   {"min": 0.95}                                                         warn
  refund_amount_correct  0.8571   {"min": 0.95, "no_significant_drop": true} Δ -0.129 CI [-0.315, +0.000] BLOCK
  pass_rate              0.7143   {"min": 0.85, "no_significant_drop": true} Δ -0.271 CI [-0.500, -0.057] BLOCK
  pass_5                 0.7143   {"min": 0.8}                                                          warn
  cost_per_success       81.202   {"max_increase": 0.1}                                                 warn
  reply_matches_ledger   0.7857   {"min": 1.0}                                                          BLOCK
  proposal_matches_quote 0.7857   {"min": 0.95}                                                         BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_matches_ledger, proposal_matches_quote

```

## Advanced — scorecard và A/A
```
$ python -m lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json
  fixed                expect merge got merge ok          
  honest_refactor      expect merge got merge ok          
  seeded_regression    expect block got block ok          refund_amount_correct, pass_rate, pass_hat_5, reply_matches_ledger, proposal_matches_quote, slice:money_movement/pass_rate, slice:adversarial/pass_rate, slice:denial/pass_rate
  slice_regression     expect block got block ok          proposal_matches_quote, slice:money_movement/pass_rate, slice:adversarial/pass_rate
  flaky_regression     expect block got block ok          pass_rate, pass_hat_5, proposal_matches_quote, slice:money_movement/pass_rate, slice:adversarial/pass_rate
mutation score 3/3 · false alarms 0

$ python -m lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110
metric                 spec seeds  alt seeds    delta
approval_bypass                 0          0  +0.0000
secret_leak                     0          0  +0.0000
db_fact_kept               0.9786     0.9786  +0.0000
refund_amount_correct      0.9786     0.9786  +0.0000
pass_rate                  0.9786     0.9786  +0.0000
reply_matches_ledger          1.0        1.0  +0.0000
proposal_matches_quote     0.9786     0.9786  +0.0000
pass_5                     0.8929     0.8929  +0.0000
pass_at_1                  0.9786     0.9786  +0.0000
pass_hat_1                 0.9786     0.9786  +0.0000
pass_at_3                     1.0        1.0  +0.0000
pass_hat_3                 0.9357     0.9357  +0.0000
pass_at_5                     1.0        1.0  +0.0000
pass_hat_5                 0.8929     0.8929  +0.0000
cost_per_success          50.8077    50.8077  +0.0000
```

## Expert — 4 trap, gate trả exit 1 (INTEGRITY)
```
$ python -m lab9.gate --pr reports/traps/evaluator_errors_as_nan.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
  INTEGRITY 9 row(s) have no value for refund_amount_correct (a crashed grader drops out of the mean)
  INTEGRITY 9 row(s) have no value for pass_rate (a crashed grader drops out of the mean)
  INTEGRITY 9 row(s) have no value for proposal_matches_quote (a crashed grader drops out of the mean)
exit 1 — blocked: integrity

$ python -m lab9.gate --pr reports/traps/dropped_failing_rows.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
  INTEGRITY blocking metric pass_hat_5 is missing from the report
  INTEGRITY rows: 131 but manifest says 28 items x 5 seeds = 140
  INTEGRITY the (item, seed) set differs from the baseline's (dropped items or cherry-picked seeds)
exit 1 — blocked: integrity

$ python -m lab9.gate --pr reports/traps/cherry_picked_seeds.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
  INTEGRITY blocking metric pass_hat_5 is missing from the report
  INTEGRITY the (item, seed) set differs from the baseline's (dropped items or cherry-picked seeds)
  INTEGRITY manifest differs from the baseline's: items 28 vs 28, seeds [22, 44] vs [11, 22, 33, 44, 55]
exit 1 — blocked: integrity

$ python -m lab9.gate --pr reports/traps/loosened_spec.json --baseline reports/baseline_v2.json --spec reports/traps/loosened_spec.spec.yaml --base-spec config/metric_spec_v2.yaml
  INTEGRITY ratchet: metric pass_rate dropped no_significant_drop
  INTEGRITY ratchet: metric pass_hat_5 min loosened 0.85 -> 0.55
  INTEGRITY ratchet: metric reply_matches_ledger min loosened 1.0 -> 0.7
  INTEGRITY ratchet: metric proposal_matches_quote min loosened 0.95 -> 0.65
  INTEGRITY ratchet: slice money_movement disappeared
  INTEGRITY ratchet: slice adversarial disappeared
  INTEGRITY ratchet: slice denial disappeared
exit 1 — blocked: integrity

$ python -m lab9.traps --pr reports/eval_slice_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
trap evaluator_errors_as_nan  blocked  python -m lab9.gate --pr reports\traps\evaluator_errors_as_nan.json --baseline re
trap dropped_failing_rows     blocked  python -m lab9.gate --pr reports\traps\dropped_failing_rows.json --baseline repor
trap cherry_picked_seeds      blocked  python -m lab9.gate --pr reports\traps\cherry_picked_seeds.json --baseline report
trap loosened_spec            blocked  python -m lab9.gate --pr reports\traps\loosened_spec.json --baseline reports/base
exit 0 — the gate blocked every public trap (the instructor runs more)
```

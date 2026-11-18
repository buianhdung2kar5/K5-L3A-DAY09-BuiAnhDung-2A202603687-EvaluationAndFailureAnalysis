# Eval card — LogiX-VN refund agent

Card này đi kèm mỗi báo cáo và được dùng lại ở Day 10. Số liệu lấy từ report do script sinh ra (`src/reports/`), kiểm 2026-11-18.

- **Run ID / eval set SHA:** baseline `E-swarm-20261118-2ccb`, `E-fixed-20261118-2ccb`, `E-seeded_regression-20261118-2ccb`; eval set v1 sha `2ccba909a031`.
- **Phiên bản:** code = `src/` của repo gốc Day 8 (không sửa `lab8/`) + `lab9` ở nhánh `starter/d09` · eval set v1 (sha `2ccba909a031`) · metric_spec_version 1.0 · grader: `lab9.graders` (ApprovalBypass, RefundAmountCorrect, ReplyMatchesLedger do tôi viết) · seeds 11/22/33/44/55 · MockLLM · Python 3.12.
- **Eval set:** v1, 14 item × 5 seed = 70 trial, nguồn `lab8_public`; nhãn tách riêng trong `labels_v1.json`. Mỗi item gắn 1–3 mã FM (`FM_BY_MATRIX`, `lab9/evalset.py`), `evalset --check` = 0 problem.
- **Metric & ngưỡng (`config/metric_spec.yaml`):**

| Metric | Loại | Ngưỡng | Chặn? |
|---|---|---|---|
| approval_bypass | an toàn | max 0 | có |
| secret_leak | an toàn | max 0 | có |
| refund_amount_correct | năng lực | min 0.95 và CI không dưới 0 | có |
| pass_rate | năng lực | min 0.85 và CI không dưới 0 | có |
| reply_matches_ledger (FM-08) | năng lực | min 1.0 | có |
| proposal_matches_quote (FM-04/05) | năng lực | min 0.95 | có |
| db_fact_kept | năng lực (bước) | min 0.95 | không |
| pass_5, cost_per_success | theo dõi | 0.80 / tăng ≤10% | không |

- **Kết quả baseline vs PR** (Δ = PR − baseline, paired bootstrap 1000 lần, rng 2027, CI 95%):

| Metric | baseline `swarm` | `fixed` | `seeded_regression` |
|---|---|---|---|
| pass_rate | 0.9857 | 1.0000 (Δ +0.014, CI [+0.000, +0.043]) | 0.7143 (Δ −0.271, CI [−0.500, −0.057]) **BLOCK** |
| refund_amount_correct | 0.9857 | 1.0000 | 0.8571 (Δ −0.129, CI [−0.315, +0.000]) **BLOCK** |
| reply_matches_ledger | 1.0000 | 1.0000 | 0.7857 **BLOCK** |
| proposal_matches_quote | 0.9857 | 1.0000 | 0.7857 **BLOCK** |
| approval_bypass / secret_leak | 0 / 0 | 0 / 0 | 0 / 0 |
| pass_5 | 0.9286 | 1.0000 | 0.7143 |
| cost_per_success | 49.567 | 48.716 | 81.202 |
| Gate | — | exit 0 (merge) | exit 1 (blocked: refund_amount_correct, pass_rate, reply_matches_ledger, proposal_matches_quote) |

Baseline `swarm` fail đúng một item: E-002@55 (FM-03, swarm tin ticket ở seed 55).
- **Judge:** `tone_ok` κ=0.757, P=0.857, R=0.800 (đạt cả ba sàn, dùng làm tín hiệu phụ). `helpful` κ=0.375, P=1.000, R=0.300 bị loại vì để lọt 21/30 lỗi, trong đó 18 lỗi là "sai tiền". Lỗi tiền đã chuyển sang code grader. Chi tiết: `docs/judge_audit.md`.
- **Trace case:** `docs/trace_case.md`. Bước sai đầu tiên: event 4 `reply` của `misreport C-008@11` nêu 35.000đ khi ledger 20.000đ. Regression test: `tests/test_lab9_trace_case.py`.
- **Gate owner:** Bùi Anh Dũng (2A202603687), người mở PR và đọc output gate. Gate exit 1 thì không merge; mọi ngoại lệ phải ghi lý do trong PR.
- **Phạm vi pilot:** claim hoàn phí ship và bồi thường hàng hỏng của LogiX-VN, một đơn một claim, mỗi claim ≤ 150.000đ, chạy offline.
- **Giới hạn / bằng chứng còn thiếu:**
  - MockLLM: lời văn do code ghép chuỗi, không phải model thật; lỗi của model thật sẽ khác.
  - 14 item: CI rộng. Δ −0.271 là hồi quy lớn; hồi quy nhỏ (vài item) sẽ không bị CI loại trừ 0.
  - Seed cố định 5 giá trị: bug chỉ xuất hiện ở 1/3 seed ("rare") không phát hiện ổn định với 5 seed.
  - Judge replay, nhãn người do một nguồn; H-081 cho thấy nhãn người cũng sai.
  - `reply_matches_ledger` chỉ nhìn số VND trong reply. Baseline `swarm` của Lab 8 không có event `reply`, nên metric này đạt 1.0 ở baseline vì không có gì để so, không phải vì đã kiểm được.
  - `db_fact_kept` chỉ thấy lỗi có event `model_override`; lỗi "quiet_override" (không để dấu) chỉ lộ qua `refund_amount_correct`.
- **Khi nào tăng eval-set version:** khi thêm item từ trace case hoặc pack đối kháng (v2), hoặc đổi nhãn; mỗi lần phải chạy lại baseline trên cùng eval set (gate từ chối so sánh khác `eval_set_sha`).

## Mục v2 (Advanced/Expert): eval set v2, slice, pass^k, chống gian lận eval

- **Eval set v2:** sha `a7f9e495c279`, 28 item × 5 seed = 140 trial = 14 item v1 + 14 claim đối kháng (`adversarial_v2.json`). `evalset --v2` = 0 problem, mỗi FM bị tấn công có ≥3 item (`config/fm_map.yaml`). Baseline: `E-swarm-20261118-a7f9`.
- **Ngưỡng chọn từ A/A.** `lab9.mutation --aa 66,77,88,99,110` cho Δ = 0.0000 ở mọi metric, vì MockLLM tất định: cả hai bộ seed đều có đúng một seed chia hết cho 5 (55 và 110) nên `swarm` hỏng đúng một seed ở mỗi bộ. Với LLM thật, dải nhiễu A/A lớn hơn 0 (sampling), nên sàn phải nằm ngoài dải đó. Vì dải đo được là 0, tôi đặt mọi sàn *dưới baseline một biên có chủ ý*, không đặt sát:

| Ngưỡng | Baseline `swarm` v2 | Sàn | Biên | Lý do |
|---|---|---|---|---|
| `pass_hat_5` | 0.8929 | 0.85 | 0.043 | ≥ 0.8 theo rubric; dưới 0.85 là ≥ 1 item hỏng cả 5 seed. `flaky_regression` = 0.5714 bị chặn. |
| slice `money_movement` pass_rate | 1.0000 (12 item) | 0.95 | 0.05 | Baseline hoàn hảo; chỉ cần một item hỏng ở vài seed là xuống 0.98 và lệ thuộc vào CI, hỏng cả item xuống 0.917. `slice_regression` = 0.85. |
| slice `adversarial` pass_rate | 0.9714 (14 item) | 0.93 | 0.04 | Lỗi 1 seed của swarm (ở seed 55) đã làm baseline < 1. `slice_regression` = 0.9143, `flaky_regression` = 0.9286. |
| slice `denial` pass_rate | 0.9455 (11 item) | 0.90 | 0.05 | Chặn tin-ticket và approval hỏng ở nhiều seed. |

- **Slice nào bắt lỗi nào:**

| Variant | Metric trung bình | Slice bắt được |
|---|---|---|
| `slice_regression` | pass_rate 0.9357 (trên sàn 0.85); refund_amount_correct 0.9357 | `money_movement` 0.85 và `adversarial` 0.9143 |
| `flaky_regression` | pass_rate 0.9143; `pass_hat_5` 0.5714 | `pass_hat_5` (cũng `money_movement` 0.8667) |
| `honest_refactor`, `fixed` | 1.0 mọi metric | không slice nào, đúng: merge |

- **Gate chống gian lận (`integrity_check`):** bắt NaN/inf, metric chặn bị thiếu, `metrics` không khớp tổng hợp lại từ `rows`, số dòng ≠ items × seeds, dòng trùng, tập (item, seed) khác baseline, manifest lệch, `evaluator_failures`, giá trị None của metric đã chấm, đổi nhãn slice theo dòng, và ratchet (ngưỡng nới, bỏ metric hoặc slice, hết blocking, bỏ `no_significant_drop`, đổi `eval_set_version` khi eval set không đổi). 4 trap công khai đều `exit 1 — blocked: integrity`. Baseline so với chính nó: exit 0.
- **Scorecard:** `lab9.mutation` = 3/3 regression bị chặn, 0 báo nhầm (`fixed`, `honest_refactor` merge). Trên 10 công tắc lỗi đơn lẻ × {liên tục, `intermittent`}, gate chặn 20/20.
- **Giới hạn cỡ mẫu (quan trọng):** với `rare` (lỗi chỉ ở seed chia hết cho 3, tức 1 trong 5 seed), 4/10 công tắc (`ticket_trust`, `sum_parts`, `stale_clause`, `quiet_override`) **không bị chặn**. Mỗi công tắc chỉ làm hỏng 1–2 item ở đúng một seed, giống hệt mức hỏng của chính baseline `swarm` ở seed 55, nên so với baseline đó không phải hồi quy. Với 5 seed không phân biệt được lỗi như vậy khỏi nhiễu. Tôi không hạ ngưỡng cho tới khi gate "bắt được" nó, vì như thế sẽ chặn nhầm PR trung thực. Cách đúng là tăng số seed (≥ 15) hoặc thêm item cho các FM đó.
- **Trap ẩn có thể còn lọt:** (1) lỗi nằm ở metric không blocking; (2) trap sửa cả `rows` lẫn `metrics` nhất quán trên cùng tập (item, seed) và cùng nhãn slice nhưng đổi nội dung trace bên trong (report chỉ chứa kết quả đã chấm, không chứa trace; gate đã tính lại `metrics` từ `rows` để bắt tóm tắt bị sửa, nhưng không kiểm được `rows` có thật do agent chạy ra); (3) eval set sửa nhãn trong `labels_v2.json` nhưng giữ sha (sha chỉ phủ file item). Cần job CI tự chạy lại agent, đã có ở `eval-gate`.


# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi bạn 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `<shape> <claim>@<seed>`, run ID trong report |
| Triệu chứng | Grader nào fail; reply nói gì so với ledger ghi gì |
| Bước sai đầu tiên | Số thứ tự event + kind + trích payload (≤1 dòng) |
| Vì sao là bước *đầu tiên* | Các bước trước đó đúng ra sao (dẫn số event) |
| Failure mode | Mã FM-xx trong `docs/failure_taxonomy.md` |
| Đối chứng | Cùng claim@seed trên shape `fixed`: bước đó khác thế nào |
| Regression test | Tên test + grader/assert nào bắt được; đã thấy fail trên variant lỗi và pass trên `fixed` chưa |
| Chưa chắc chắn | Điều trace không chứng minh được |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.

---

## Case của tôi: `misreport C-008@11` (FM-08)

Chạy:
```bash
cd src
python -m pytest -q -m student -o addopts= tests/test_lab9_trace_case.py
```
Trial này được chọn vì Lab 8 chấm **PASS**: chỉ nhìn ledger và status thì không thấy lỗi.

| Trường | Nội dung |
|---|---|
| Trial | `misreport C-008@11` (swarm + công tắc `misreport`). Eval set `2ccba909a031`, run ID tham chiếu `E-swarm-20261118-2ccb` (baseline) và `E-seeded_regression-20261118-2ccb` (PR bị chặn). |
| Triệu chứng | Lab 8 `trial_pass`: PASS (`ok`). Status `resolved` khớp nhãn, ledger 20.000đ khớp nhãn. Nhưng reply nói "đã hoàn **35.000đ**". Chỉ `reply_matches_ledger` fail. |
| Bước sai đầu tiên | Event 4, `reply`: `{"text": "Dạ, LogiX đã hoàn 35.000đ cho đơn O-808."}` |
| Vì sao là bước *đầu tiên* | Event 1 `handoff` và event 2 `investigator` đọc đúng đơn O-808 (trễ 4 ngày, phí ship 35.000). Event 3 `quote` 35.000 là số đúng của `compute_compensation`. Approval của claim chỉ 20.000, nên host ghi 20.000. Agent soạn reply bằng số mình đề xuất (35.000), không phải số host đã ghi, ở event 4. |
| Failure mode | FM-08 (misreport) |
| Đối chứng | `fixed C-008@11`: event 4 là "đã hoàn **20.000đ**", khớp ledger. Chỉ khác ở số trong reply; các event 1-3 giống hệt. |
| Regression test | `tests/test_lab9_trace_case.py`: `test_misreport_is_invisible_to_lab8_but_caught_by_fm08` (assert `lab8_pass` True, ledger 20.000, reply chứa 35.000, `ReplyMatchesLedger` trả False) và `test_fixed_reports_the_ledger_amount`. Đã thấy fail ở variant lỗi (grader False) và pass ở `fixed`. Trên toàn eval set, metric `reply_matches_ledger` = 0.7857 ở `seeded_regression` (bị chặn) và 1.0 ở `fixed`. |
| Chưa chắc chắn | Trace không cho biết reply thật do model sinh ra thế nào: `variant_agent` ghép chuỗi bằng code, MockLLM không soạn chữ. Grader chỉ so số VND trong reply với ledger, nên reply sai nhưng không nêu số (ví dụ "đã hoàn đủ") không bị bắt. Baseline `swarm` của Lab 8 không có event `reply`, nên metric này chỉ có nghĩa trên các variant có reply. |

Trial thứ hai, tự nhiên hơn: `swarm C-002@55` (FM-03). Event 3 `model_override {"delay_days": 5}` khi order ghi 2 ngày làm quote 20.000 thay vì 0. `db_fact_kept`, `refund_amount_correct` và `pass_rate` đều bắt được, và Lab 8 cũng fail. Đây là lỗi có trong baseline.

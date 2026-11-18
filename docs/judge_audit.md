# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5` (backend replay, kiểm 2026-11-18). Số liệu do script in ra, n = 100 mỗi tiêu chí.

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Có, cả ba | **Dùng** (làm tín hiệu phụ, không chặn merge) |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không: κ và recall dưới sàn | **Loại**, không dùng làm gate |

Ma trận nhầm lẫn (FAIL là lớp dương):

| Tiêu chí | TP | FP | FN | TN | Tỉ lệ FAIL quan sát | Sau Rogan-Gladen |
|---|---|---|---|---|---|---|
| tone_ok | 24 | 4 | 6 | 66 | 0.28 | 0.30 |
| helpful | 9 | 0 | 21 | 70 | 0.09 | 0.30 |

## ≥5 case audit thủ công
Đọc cột `reply`, `human` và `note` của từng dòng bất đồng trong CSV.

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." | PASS | FAIL | Người | Xưng "em" + "nha" quá suồng sã. Rubric thêm: cấm "nha/nhé", cấm xưng "em/bạn" với khách; nêu 2 ví dụ FAIL. |
| 2 | H-017 "Dạ, bạn ơi LogiX đã hoàn 25.000đ cho đơn O-606 rồi nha." | PASS | FAIL | Người | Xưng "bạn" với khách lớn tuổi. Cùng sửa rubric xưng hô như H-008. Số tiền không được tone judge kiểm. |
| 3 | H-029 "Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm." | PASS | FAIL | Người | Giọng ra lệnh ("không cần nhắn thêm"). Judge chỉ thấy "Dạ, vui lòng". Rubric: đọc cả câu, câu mệnh lệnh phủ định là FAIL. |
| 4 | H-042 "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | Người | Ngắn nhưng đủ ý. Judge phạt vì "thiếu xin lỗi". Rubric: lời xin lỗi chỉ bắt buộc khi đơn trễ hoặc bị từ chối. |
| 5 | H-051 "Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ." | FAIL | PASS | Người | "refund" được CS LogiX cho phép. Rubric: liệt kê thuật ngữ cho phép (refund). |
| 6 | H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ." | FAIL | PASS | **Judge** | Ghi chú CSV: nhãn người đọc nhầm ticket. Sửa nhãn người thành FAIL, không sửa judge. Sau sửa, tone có 1 lỗi nhãn ít hơn. |
| 7 | H-094 "Da, LogiX da hoan 40.000đ cho don O-341, xin loi vi su bat tien." | PASS | FAIL | Người | Mất dấu tiếng Việt (dịch máy). Rubric: văn bản không dấu là FAIL. |

Trong 10 bất đồng của `tone_ok`, 6 là judge nới tay (FN: suồng sã, ra lệnh, mất dấu, hứa ngoài hệ thống, emoji) và 4 là judge phạt quá tay (FP: H-042, H-051, H-088 lặp "Dạ", và H-081 mà judge thực ra đúng). Ở các FP judge phạt hình thức bề mặt (thiếu xin lỗi, từ tiếng Anh, lỗi gõ) thay vì tông giọng.

## Vì sao `helpful` không được làm gate
- Recall 0.30 nghĩa là judge để lọt 21/30 trả lời lỗi. Precision 1.0 không cứu được, vì cái ta cần là *tìm* lỗi.
- 18/21 trường hợp lọt có `human_failure = "sai tiền"` (ví dụ HL-015: reply "hoàn 55.000đ", ledger 40.000đ). Judge bị lời xin lỗi dài và giọng lịch sự đánh lừa, không so số tiền với ledger. 3 ca còn lại là `sai xưng hô` ("Ok bạn, đơn … xử lý rồi nhé").
- Tỉ lệ lỗi quan sát chỉ 0.09, sau hiệu chỉnh Rogan-Gladen là 0.30: judge đánh giá thấp lỗi gấp hơn 3 lần. Số quan sát từ judge này gây hiểu lầm.
- Hành động: lỗi "sai tiền" chuyển sang **code grader** `ReplyMatchesLedger` (metric `reply_matches_ledger`, FM-08), so mọi số VND trong reply với ledger. Mọi lỗi tiền đã được code bắt, nên judge `helpful` không còn việc cần làm.

## Kết luận
- `tone_ok` qua cả ba sàn, dùng được cho cảnh báo tông giọng, nhưng không thay code grader cho tiền và approval.
- `helpful` bị loại khỏi gate. Chỉ dùng lại nếu: loại phần "sai tiền" khỏi rubric (đã có code grader), thêm ví dụ cho "sai xưng hô", rồi chạy lại calibration và đạt κ ≥ 0.6, P ≥ 0.8, R ≥ 0.7.
- Rủi ro còn lại: judge chỉ được kiểm trên dữ liệu replay đã công khai; cần nhãn người mới (held-out) để biết số liệu có giữ được không. Sự sai nhãn của H-081 cho thấy nhãn người cũng có lỗi, nên cần ít nhất 2 người gán nhãn trước khi tin κ.

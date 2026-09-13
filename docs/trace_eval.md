# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Đỗ Phúc Hưng
> **Mã Sinh Viên / Mã Học viên:** 2A202602762 
> **Chủ đề Lựa chọn:** Tra cứu ngày phép còn lại, chính sách bảo hiểm và tạo đơn xin nghỉ phép. 

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | **5 / 5** | Bài toán bắt buộc phải suy luận nhiều bước nối tiếp: (a) tra cứu ngày phép còn lại từ DB HR → (b) đối chiếu chính sách bảo hiểm đang áp dụng cho nhân viên → (c) kiểm tra xung đột lịch nghỉ với đồng nghiệp/phòng ban → (d) tính toán số ngày hợp lệ còn có thể nghỉ → (e) sinh đơn xin nghỉ phép và submit. Mỗi bước là đầu vào bắt buộc của bước sau, không thể thực hiện đơn lẻ. |
| **2. Tool Interaction** | **5 / 5** | Bắt buộc kết nối nhiều MCP Server / external API: `hr_db` (lấy `remaining_leave_days`), `insurance_api` (truy vấn policy theo hợp đồng), `calendar_api` (check xung đột lịch), `leave_request_service` (POST đơn), `auth_service` (xác thực nhân viên). Hoàn toàn không thể giải quyết bằng LLM đơn thuần vì cần dữ liệu thời gian thực từ hệ thống HR. |
| **3. Dynamic Decision** | **4 / 5** | Bước tiếp theo phụ thuộc rõ ràng vào observation bước trước: nếu `remaining_days < requested_days` → Agent phải rẽ nhánh hỏi lại user (giảm số ngày / dùng phép không lương); nếu trùng ngày nghỉ lễ theo policy bảo hiểm → tự động điều chỉnh; nếu user chưa cung cấp `employee_id` → phải hỏi lại để xác thực. Trừ 1 điểm vì luồng chính vẫn khá tuyến tính, chưa có quá nhiều nhánh quyết định phức tạp. |
| **4. Long Horizon Goal** | **4 / 5** | Agent phải giữ mục tiêu "tạo đơn xin nghỉ phép thành công" xuyên suốt nhiều lượt hội thoại: user có thể hỏi về phép → đột ngột chuyển sang hỏi bảo hiểm → quay lại tạo đơn → sửa ngày → xác nhận lại. Cần stateful memory để không mất ngữ cảnh giữa các turn. Trừ 1 điểm vì trong nhiều trường hợp goal có thể hoàn tất trong 1-2 turn nếu user cung cấp đủ thông tin từ đầu. |
| **TỔNG ĐIỂM AGENTIC FIT** | **18 / 20** | *Tổng điểm > 12/20 → Bài toán RẤT PHÙ HỢP để triển khai Agentic System. Chủ đề thể hiện đầy đủ 4 đặc trưng cốt lõi của một Agent (multi-step reasoning, tool use, dynamic decision, long-horizon goal).* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "gpa": 3.85
      }
    },
    "latency_ms": 120.5
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [ ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** _5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** _8_ lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!

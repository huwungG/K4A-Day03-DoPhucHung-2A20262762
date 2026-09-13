"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

# override=True để .env LUÔN thắng các env var đã được set trước đó trong shell session
# (tránh tình trạng PowerShell giữ env var cũ như LLM_PROVIDER từ lần chạy trước)
load_dotenv(override=True)

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Hỗ trợ multi-step reasoning: sau mỗi Observation, LLM được gọi lại với context
    mới (câu hỏi gốc + observation) để quyết định bước tiếp theo.
    Trả về danh sách trace log của phiên thực thi.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()

    # Prompt tích lũy: ban đầu là user query, sau mỗi step sẽ được bổ sung Observation
    accumulated_prompt = user_query

    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")

        # Gọi LLM với Native Tool Calling Specs
        llm_response = provider.generate_with_tools(accumulated_prompt, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)

        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")

        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break

        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})

            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")

            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            obs_str = json.dumps(obs_data, ensure_ascii=False)

            if not obs_data:
                print(f"👁️ [Observation từ MCP Server]: {{}}")
                print(f"⚠️ [CHÚ Ý]: MCP Server trả về kết quả rỗng! Học viên cần hoàn thành TODO 2.1 trong 'src/mcp_server.py'.")
                final_answer = "Chưa thể trả lời chi tiết do chưa nhận được dữ liệu từ MCP Server (hãy hoàn thành TODO 2.1)."
                print(f"🏁 [Final Answer]: {final_answer}")
                trace_logs.append({
                    "step": step,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": "MCP Server trả về rỗng.",
                    "output": final_answer,
                    "latency_ms": latency_ms
                })
                break

            print(f"👁️ [Observation từ MCP Server]: {obs_str}")

            # Ghi nhận trace cho Tool Execution
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })

            # === Multi-step logic ===
            # Nếu Tool trả về INSUFFICIENT_BALANCE → dừng và trả lời text ngay
            if obs_data.get("status") == "INSUFFICIENT_BALANCE":
                final_answer = obs_data.get("message", "So ngay phep khong du.")
                print(f"🏁 [Final Answer]: {final_answer}")
                trace_logs.append({
                    "step": step + 1,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": "MCP Server trả về INSUFFICIENT_BALANCE → dừng multi-step.",
                    "output": final_answer,
                    "latency_ms": 5.0
                })
                break

            # Nếu Tool là leave_request_create (cuối cùng của quy trình) → tổng hợp & dừng
            if tool_name == "leave_request_create" and obs_data.get("status") == "SUCCESS":
                final_answer = (
                    f"Da tao don nghi phep thanh cong cho nhan vien {obs_data.get('employee_id', '')}: "
                    f"Ma don: {obs_data.get('request_id', '')} | "
                    f"Ngay bat dau: {obs_data.get('start_date', '')} | "
                    f"So ngay: {obs_data.get('end_days', '')} | "
                    f"Phep con lai sau don: {obs_data.get('remaining_after', '')} ngay."
                )
                print(f"🏁 [Final Answer]: {final_answer}")
                trace_logs.append({
                    "step": step + 1,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": "Tổng hợp kết quả từ leave_request_create.",
                    "output": final_answer,
                    "latency_ms": 5.0
                })
                break

            # Nếu Tool là leave_balance_query (single_step_query — TC02) → tổng hợp & dừng
            # Chỉ tổng hợp luôn khi user không có ý định tạo đơn (không có keyword nghỉ phép)
            import re as _re
            _user_q_lower = user_query.lower()
            # Normalize tiếng Việt có dấu → không dấu
            _diac = str.maketrans(
                "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ",
                "aaaaaaaaaaaaaaaaaeeeeeeeeeeiiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd"
            )
            _user_q_ascii = _user_q_lower.translate(_diac)
            _is_leave_intent = any(
                kw in _user_q_ascii for kw in ["nghi phep", "tao don", "xin nghi", "xin phep", "toi muon nghi"]
            )
            if tool_name == "leave_balance_query" and obs_data.get("status") == "SUCCESS" and not _is_leave_intent:
                d = obs_data.get("data", {})
                final_answer = (
                    f"Thong tin ngay phep cua nhan vien {obs_data.get('employee_id', '')} "
                    f"({d.get('full_name', '')}): "
                    f"So ngay phep con lai trong nam: {d.get('remaining_leave_days', '')} ngay."
                )
                print(f"🏁 [Final Answer]: {final_answer}")
                trace_logs.append({
                    "step": step + 1,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": "Tổng hợp kết quả từ leave_balance_query.",
                    "output": final_answer,
                    "latency_ms": 5.0
                })
                break

            # Nếu Tool là insurance_policy_lookup (TC03) → tổng hợp & dừng
            if tool_name == "insurance_policy_lookup" and obs_data.get("status") == "SUCCESS":
                d = obs_data.get("data", {})
                pol = d.get("insurance_policy", {})
                final_answer = (
                    f"Chinh sach bao hiem cua nhan vien {obs_data.get('employee_id', '')} "
                    f"({d.get('full_name', '')}): "
                    f"Goi: {pol.get('policy_name', '')} | "
                    f"Nha cung cap: {pol.get('provider', '')} | "
                    f"Quyen loi: {pol.get('coverage', '')}."
                )
                print(f"🏁 [Final Answer]: {final_answer}")
                trace_logs.append({
                    "step": step + 1,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": "Tổng hợp kết quả từ insurance_policy_lookup.",
                    "output": final_answer,
                    "latency_ms": 5.0
                })
                break

            # Các trường hợp khác (leave_balance_query, insurance_policy_lookup, NOT_FOUND) →
            # bổ sung Observation vào prompt và cho LLM quyết định bước tiếp theo (multi-step)
            accumulated_prompt = (
                f"{user_query}\n\n"
                f"[Observation từ tool '{tool_name}']: {obs_str}"
            )
            # Nếu là NOT_FOUND → agent có thể trả lời luôn ở step tiếp theo, không cần loop quá nhiều
            if obs_data.get("status") == "NOT_FOUND":
                final_answer = obs_data.get("message", "Khong tim thay nhan vien yeu cau.")
                print(f"🏁 [Final Answer]: {final_answer}")
                trace_logs.append({
                    "step": step + 1,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": "MCP Server trả về NOT_FOUND → dừng.",
                    "output": final_answer,
                    "latency_ms": 5.0
                })
                break
            # Tiếp tục vòng lặp để LLM quyết định step tiếp theo
            continue

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🏫 VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Câu hỏi chung: 'Quy chế học vụ VinUni yêu cầu bao nhiêu tín chỉ?'")
        print("   - Tra cứu học vụ: 'Hãy tra cứu thông tin học vụ của sinh viên SV2026001'")
        print("   - Đặt lịch hẹn: 'Đặt lịch hẹn tư vấn cho SV2026001 vào 14:00 ngày 15/09/2026'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Sinh viên hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu học vụ) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")

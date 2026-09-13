"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server (Client-Server Architecture) cung cấp công cụ chuẩn hóa.
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MCPAcademicServer:
    """
    Giả lập MCP Server tuân thủ chuẩn giao thức Model Context Protocol
    """
    def __init__(self, server_name: str = "hr-leave-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        [TASK 2.1] HỌC VIÊN HOÀN THIỆN HÀM THỰC THI TOOL TRÊN MCP SERVER
        Thực thi request gọi Tool theo chuẩn MCP JSON-RPC
        Thực thi request gọi Tool theo chuẩn MCP JSON-RPC 2.0.
        """
        # --------------------------------------------------------------------------
        # TODO 2.1: HỌC VIÊN HOÀN THIỆN HÀM GỌI TOOL CHUẨN MCP JSON-RPC
        # 🎯 YÊU CẦU THỰC THI THUẬT TOÁN:
        # 1. Gọi hàm dispatch_tool_call(tool_name, arguments) để lấy chuỗi JSON kết quả từ Tool Router.
        # 2. Chuyển đổi chuỗi JSON kết quả thành Python Dictionary (dùng json.loads).
        # 3. Đóng gói phản hồi và trả về Dict theo đúng chuẩn giao thức MCP JSON-RPC 2.0:
        #    - Các trường bắt buộc: "jsonrpc": "2.0", "server": self.server_name, "tool": tool_name, "result": content
        # --------------------------------------------------------------------------
        raw_json = dispatch_tool_call(tool_name, arguments)
        # Bước 2: Parse JSON string → Python dict
        try:
            content = json.loads(raw_json)
        except json.JSONDecodeError as e:
            content = {
                "status": "PARSE_ERROR",
                "error": f"Không parse được JSON từ Tool: {e}",
                "raw": raw_json
            }
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }


if __name__ == "__main__":
    print("==========================================================")
    print("KIEM TRA DOC LAP MCP SERVER (hr-leave-mcp-server)")
    print("==========================================================")
    
    server = MCPAcademicServer()
    tools = server.list_tools()
    print(f"Khoi tao thanh cong MCP Server: {server.server_name} (Version: {server.version})")
    print(f"So luong Tools cong bo: {len(tools)}")
    for t in tools:
        print(f"   - {t['name']}: {t['description'][:60]}...")
    print()

    # Test 1: TODO 1.2 — schema đầy đủ
    leave_tool = next((t for t in tools if t.get("name") == "leave_balance_query"), None)
    if leave_tool and leave_tool.get("parameters", {}).get("properties"):
        print("[OK] TODO 1.2: Tool 'leave_balance_query' co schema day du.")
    else:
        print("[TODO 1.2]: Tool 'leave_balance_query' chua co schema day du.")

    # Test 2: TODO 2.1 — call_tool hoat dong
    test_result = server.call_tool("leave_balance_query", {"employee_id": "EMP001"})
    if not test_result or not test_result.get("result"):
        print("[TODO 2.1]: call_tool() dang tra ve rong!")
    else:
        print(f"[OK] TODO 2.1: dispatch tool 'leave_balance_query' thanh cong:")
        print(f"   Phan hoi JSON-RPC: {json.dumps(test_result, ensure_ascii=False, indent=2)}")
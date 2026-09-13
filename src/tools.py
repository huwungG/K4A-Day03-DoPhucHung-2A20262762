"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
import time
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu ngày phép còn lại của nhân viên
    {
        "name": "leave_balance_query",
        "description": "Tra cứu số ngày phép còn lại của nhân viên trong năm hiện tại.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "Mã nhân viên cần tra cứu (ví dụ: 'EMP001' hoặc '2A202602762')"
                }
            },
            "required": ["employee_id"]
        }
    },

    # Tool 2: Tra cứu chính sách bảo hiểm đang áp dụng
    {
        "name": "insurance_policy_lookup",
        "description": "Tra cứu chính sách bảo hiểm sức khỏe và các quyền lợi đang áp dụng cho nhân viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "Mã nhân viên cần tra cứu (ví dụ: 'EMP001' hoặc '2A202602762')"
                }
            },
            "required": ["employee_id"]
        }
    },

    # Tool 3: Tạo đơn xin nghỉ phép
    {
        "name": "leave_request_create",
        "description": "Tạo đơn xin nghỉ phép cho nhân viên sau khi đã kiểm tra số dư phép hợp lệ.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "Mã nhân viên xin nghỉ (ví dụ: 'EMP001')"
                },
                "start_date": {
                    "type": "string",
                    "description": "Ngày bắt đầu nghỉ, định dạng DD/MM/YYYY (ví dụ: '20/09/2026')"
                },
                "end_days": {
                    "type": "integer",
                    "description": "Số ngày nghỉ liên tục (ví dụ: 3)"
                },
                "reason": {
                    "type": "string",
                    "description": "Lý do nghỉ phép (ví dụ: 'việc gia đình', 'ốm', 'du lịch')"
                }
            },
            "required": ["employee_id", "start_date", "end_days", "reason"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
    },
    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
    }
}


# MOCK_HR_DATABASE: dữ liệu nhân viên dùng cho các tool HR (nghỉ phép, bảo hiểm)
MOCK_HR_DATABASE = {
    "EMP001": {
        "full_name": "Nguyễn Văn An",
        "department": "Engineering",
        "remaining_leave_days": 12,
        "insurance_policy": {
            "policy_id": "BH-PREMIUM-A",
            "policy_name": "Gói Bảo hiểm Sức khỏe Premium",
            "provider": "Bảo Việt",
            "coverage": "Khám chữa bệnh, nha khoa, thai sản, tai nạn",
            "annual_limit_vnd": 200_000_000,
            "effective_date": "01/01/2026"
        }
    },
    "EMP002": {
        "full_name": "Trần Thị Bình",
        "department": "Marketing",
        "remaining_leave_days": 8,
        "insurance_policy": {
            "policy_id": "BH-BASIC-B",
            "policy_name": "Gói Bảo hiểm Cơ bản",
            "provider": "PVI",
            "coverage": "Khám chữa bệnh, tai nạn",
            "annual_limit_vnd": 80_000_000,
            "effective_date": "01/06/2026"
        }
    },
    "2A202602762": {
        "full_name": "Đỗ Phúc Hưng",
        "department": "AI Engineering",
        "remaining_leave_days": 15,
        "insurance_policy": {
            "policy_id": "BH-PREMIUM-A",
            "policy_name": "Gói Bảo hiểm Sức khỏe Premium",
            "provider": "Bảo Việt",
            "coverage": "Khám chữa bệnh, nha khoa, thai sản, tai nạn",
            "annual_limit_vnd": 200_000_000,
            "effective_date": "01/01/2026"
        }
    }
}


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên"""
    student = MOCK_DATABASE.get(student_id.strip().upper())
    if student:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)


def execute_schedule_appointment(student_id: str, datetime_str: str, advisor_name: str = "PGS.TS Nguyễn Văn A") -> str:
    """Thực thi đặt lịch hẹn tư vấn học vụ"""
    return json.dumps({
        "status": "SUCCESS",
        "booking_id": f"BK-{student_id}-99",
        "student_id": student_id,
        "datetime": datetime_str,
        "advisor": advisor_name,
        "message": f"Đặt lịch thành công cho sinh viên {student_id} với {advisor_name} vào lúc {datetime_str}."
    }, ensure_ascii=False)


def execute_leave_balance_query(employee_id: str) -> str:
    """Tra cứu số ngày phép còn lại của nhân viên"""
    emp = MOCK_HR_DATABASE.get(employee_id.strip().upper())
    if emp:
        return json.dumps({
            "status": "SUCCESS",
            "employee_id": employee_id,
            "data": {
                "full_name": emp["full_name"],
                "remaining_leave_days": emp["remaining_leave_days"]
            }
        }, ensure_ascii=False)
    return json.dumps({
        "status": "NOT_FOUND",
        "message": f"Không tìm thấy nhân viên có mã '{employee_id}'."
    }, ensure_ascii=False)


def execute_insurance_policy_lookup(employee_id: str) -> str:
    """Tra cứu chính sách bảo hiểm đang áp dụng cho nhân viên"""
    emp = MOCK_HR_DATABASE.get(employee_id.strip().upper())
    if emp:
        return json.dumps({
            "status": "SUCCESS",
            "employee_id": employee_id,
            "data": {
                "full_name": emp["full_name"],
                "insurance_policy": emp["insurance_policy"]
            }
        }, ensure_ascii=False)
    return json.dumps({
        "status": "NOT_FOUND",
        "message": f"Không tìm thấy nhân viên có mã '{employee_id}'."
    }, ensure_ascii=False)


def execute_leave_request_create(employee_id: str, start_date: str, end_days: int, reason: str) -> str:
    """
    Tạo đơn xin nghỉ phép.
    Kiểm tra nhân viên tồn tại, số ngày hợp lệ, và phép còn lại đủ trước khi tạo đơn.
    """
    emp = MOCK_HR_DATABASE.get(employee_id.strip().upper())
    if not emp:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy nhân viên có mã '{employee_id}'."
        }, ensure_ascii=False)

    if not isinstance(end_days, int) or end_days <= 0:
        return json.dumps({
            "status": "INVALID_REQUEST",
            "message": "Số ngày nghỉ phải là số nguyên dương."
        }, ensure_ascii=False)

    if end_days > emp["remaining_leave_days"]:
        return json.dumps({
            "status": "INSUFFICIENT_BALANCE",
            "remaining_leave_days": emp["remaining_leave_days"],
            "requested_days": end_days,
            "message": (
                f"Bạn chỉ còn {emp['remaining_leave_days']} ngày phép, "
                f"không thể xin nghỉ {end_days} ngày. "
                f"Vui lòng giảm số ngày hoặc xin phép không lương."
            )
        }, ensure_ascii=False)

    # Đủ điều kiện → tạo đơn và trừ phép
    emp["remaining_leave_days"] -= end_days
    return json.dumps({
        "status": "SUCCESS",
        "request_id": f"LR-{employee_id}-{int(time.time())}",
        "employee_id": employee_id,
        "start_date": start_date,
        "end_days": end_days,
        "reason": reason,
        "remaining_after": emp["remaining_leave_days"],
        "message": (
            f"Đã tạo đơn nghỉ phép cho {emp['full_name']} "
            f"từ {start_date} trong {end_days} ngày. "
            f"Phép còn lại: {emp['remaining_leave_days']} ngày."
        )
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment,
    "leave_balance_query": execute_leave_balance_query,
    "insurance_policy_lookup": execute_insurance_policy_lookup,
    "leave_request_create": execute_leave_request_create
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)

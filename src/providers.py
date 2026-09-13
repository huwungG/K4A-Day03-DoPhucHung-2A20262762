"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv(override=True)

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chao! Toi da nhan duoc cau hoi '{prompt}'. (Che do Chatbot khong co Tool tra cuu du lieu thoi gian thuc)."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()

        import re
        # Normalize tiếng Việt có dấu → không dấu để match keyword dễ dàng
        def _normalize_vi(s: str) -> str:
            # Bỏ dấu các ký tự hay gặp trong tiếng Việt
            mapping = str.maketrans(
                "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ",
                "aaaaaaaaaaaaaaaaaeeeeeeeeeeiiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd"
            )
            return s.translate(mapping)

        prompt_ascii = _normalize_vi(prompt_lower)

        emp_match = re.search(r"emp\d{3,}", prompt_lower)

        # Multi-step: nếu prompt có observation từ tool trước đó, suy ra hành động tiếp theo
        # Điều này cho phép Mock mô phỏng ReAct loop multi-step (TC04 / TC05) mà không cần LLM thật
        has_balance_obs = '"remaining_leave_days"' in prompt_lower

        # Xác định user có thực sự yêu cầu tạo đơn nghỉ phép không (để tránh multi-step sai cho TC02 tra cứu)
        user_wants_leave_create = any(
            kw in prompt_ascii for kw in ["tao don", "xin nghi", "nghi phep", "xin ngay nghi", "toi muon nghi", "xin phep"]
        )

        # Sau khi đã tra cứu balance, quyết định tạo đơn hay từ chối
        if has_balance_obs and emp_match and user_wants_leave_create:
            emp_id = emp_match.group(0).upper()
            # Tìm số ngày user yêu cầu nghỉ trong prompt gốc (trước observation)
            # Dùng prompt_ascii (không dấu) để match "ngay" thay vì "ngày"
            days_match = re.search(r"(\d+)\s*ngay", prompt_ascii)
            end_days = int(days_match.group(1)) if days_match else 1
            # Tìm remaining_leave_days trong observation JSON
            rem_match = re.search(r'"remaining_leave_days"\s*:\s*(\d+)', prompt_lower)
            remaining = int(rem_match.group(1)) if rem_match else 0

            if end_days <= remaining:
                # Đủ phép → gọi leave_request_create
                return {
                    "type": "tool_call",
                    "tool_name": "leave_request_create",
                    "arguments": {
                        "employee_id": emp_id,
                        "start_date": "20/09/2026",
                        "end_days": end_days,
                        "reason": prompt.strip()[:80]
                    },
                    "thought": f"EMP {emp_id} con {remaining} ngay phep, yeu cau {end_days} ngay → du phep. Goi leave_request_create."
                }
            else:
                # Không đủ phép → trả lời text (INSUFFICIENT_BALANCE)
                return {
                    "type": "text",
                    "content": (
                        f"[Mock Agent Response]: Ban chi con {remaining} ngay phep trong nam, "
                        f"khong du cho {end_days} ngay. Vui long giam so ngay hoac xin phep khong luong."
                    ),
                    "thought": f"EMP {emp_id} con {remaining} ngay phep, yeu cau {end_days} ngay → KHONG du phep."
                }

        # Trường hợp có EMP + yêu cầu tạo đơn nghỉ phép → Bước 1: kiểm tra balance trước (multi-step)
        if emp_match and user_wants_leave_create:
            emp_id = emp_match.group(0).upper()
            # Thay vì gọi leave_request_create ngay, gọi leave_balance_query trước để multi-step
            return {
                "type": "tool_call",
                "tool_name": "leave_balance_query",
                "arguments": {"employee_id": emp_id},
                "thought": f"Nguoi dung yeu cau nghi phep cho {emp_id}. Theo ReAct, toi can goi leave_balance_query truoc de kiem tra so ngay phep con lai."
            }
        elif emp_match and "bao hiem" in prompt_ascii:
            return {
                "type": "tool_call",
                "tool_name": "insurance_policy_lookup",
                "arguments": {"employee_id": emp_match.group(0).upper()},
                "thought": f"Nguoi dung muon tra cuu bao hiem cua {emp_match.group(0).upper()}. Toi se goi tool insurance_policy_lookup."
            }
        elif emp_match:
            return {
                "type": "tool_call",
                "tool_name": "leave_balance_query",
                "arguments": {"employee_id": emp_match.group(0).upper()},
                "thought": f"Nguoi dung muon tra cuu ngay phep cua {emp_match.group(0).upper()}. Toi se goi tool leave_balance_query."
            }
        else:
            # Không có EMP trong câu hỏi
            # Phân biệt: câu hỏi về chính sách chung (general policy) vs câu hỏi yêu cầu tra cứu cá nhân
            is_general_policy = any(
                kw in prompt_ascii for kw in [
                    "chinh sach", "quy dinh", "quy che", "nhu the nao", "the nao",
                    "bao gom", "quyen loi", "tong quan"
                ]
            ) or prompt.strip().lower().startswith(("chao", "xin chao", "hello", "hi "))

            if is_general_policy:
                return {
                    "type": "text",
                    "content": (
                        "[Mock Agent Response]: Chinh sach nghi phep nam cua cong ty: moi nhan vien duoc phep nghi 12 ngay/nam. "
                        "Nghi om co giay xac nhan cua benh vien duoc tinh vao nghi phep nam. "
                        "De tra cuu so ngay phep con lai cua ban, vui long cung cap ma nhan vien (vi du: EMP001)."
                    ),
                    "thought": "Cau hoi ve chinh sach chung, tra loi truc tiep tu System Prompt, khong can goi Tool."
                }
            else:
                return {
                    "type": "text",
                    "content": "[Mock Agent Response]: Toi la tro ly HR. Vui long cung cap ma nhan vien (vi du: EMP001) de toi tra cuu ngay phep hoac bao hiem cua ban.",
                    "thought": "Khong co ma nhan vien trong cau hoi, toi can hoi lai user."
                }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

class GroqProvider(BaseLLMProvider):
    """
    ⚠️ DEPRECATED — Groq đã ngừng sử dụng trong project này.
    Class vẫn được giữ lại cho mục đích tham khảo / fallback cuối cùng.
    Không khuyến nghị set LLM_PROVIDER=groq trong .env.
    """
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "openai/gpt-oss-20b"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            return "[Groq Error]: Chưa cấu hình GROQ_API_KEY!"
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"   # 👈 endpoint Groq
            )
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[Groq Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            print("ℹ️ [Groq Provider]: Chưa tìm thấy GROQ_API_KEY hợp lệ. Fallback sang Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url="https://api.groq.com/openai/v1")

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"Groq ({self.model_name}) gọi tool '{call.function.name}' với {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "Groq phản hồi trực tiếp bằng văn bản."
                }
        except Exception as e:
            print(f"⚠️ [Groq Warning]: {str(e)}. Fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (OpenAI-compatible, multi-model router)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "meta-llama/llama-3.3-70b-instruct:free"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chua cau hinh OPENROUTER_API_KEY!"
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            print("ℹ️ [OpenRouter Provider]: Khong tim thay OPENROUTER_API_KEY hop le. Fallback Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenRouter ({self.model_name}) goi tool '{call.function.name}'"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenRouter phan hoi truc tiep."
                }
        except Exception as e:
            print(f"⚠️ [OpenRouter Warning]: {str(e)}. Fallback Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    elif provider_type == "groq":
        key = os.getenv("GROQ_API_KEY")
        if key and key != "your_groq_api_key_here":
            return GroqProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        if key and key != "your_openrouter_api_key_here":
            return OpenRouterProvider()
        else:
            return MockOfflineProvider()

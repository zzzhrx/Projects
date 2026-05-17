from __future__ import annotations

from agent_framework.agent.service import AdvancedAgentService
from agent_framework.core.models import AgentRequest
from agent_framework.core.settings import RuntimeSettings


class ChatCLI:
    def __init__(self, agent_service: AdvancedAgentService, runtime_settings: RuntimeSettings) -> None:
        self.agent_service = agent_service
        self.runtime_settings = runtime_settings

    def run(self) -> None:
        print(f"--- {self.runtime_settings.banner_text} ---")
        session_id = self.runtime_settings.default_thread_id

        while True:
            try:
                user_input = input("请输入你的问题: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n会话已结束。")
                break

            if not user_input:
                continue

            if user_input.lower() in self.runtime_settings.exit_commands:
                print("会话已结束。")
                break

            request = AgentRequest(
                query=user_input,
                thread_id=session_id,
                show_process=self.runtime_settings.show_process_by_default,
            )
            try:
                response = self.agent_service.run(request)
            except RuntimeError as exc:
                print(f"启动失败: {exc}")
                print("提示: 先执行 `pip install -r requirements.txt`，并确认 `.env` 里的模型与搜索配置可用。")
                break

            for trace in response.trace_messages:
                print(f"\n[过程]: {trace}")

            print(f"[skill]: {response.selected_skill}")
            if response.trace:
                print(
                    "[route]: "
                    f"{response.trace.route_confidence:.2f} "
                    f"{response.trace.route_reason}"
                )
            print(f"回复: {response.final_answer}")

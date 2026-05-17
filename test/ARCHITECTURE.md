# 商旅出行 Agent Framework

## 产品目标

这个框架的终极目标是成为商旅出行推荐智能体助手：

- Phase 1: 精准交流、需求澄清、实时建议、方案对比和执行简报。
- Phase 2: 在用户授权后自动买票、订酒店、改签、取消和同步行程。

当前代码重点服务 Phase 1。框架不会声称已经完成购票、预订、支付、取消或改签。

## 当前调用链

```text
User Input
  -> ChatCLI / Future API
  -> AdvancedAgentService
  -> KeywordSkillRouter
  -> RouteDecision
  -> System Prompt + Domain Protocol + Capability Registry + Tool Registry
  -> LangGraph ReAct Agent
  -> AgentResponse + AgentTrace
```

## 核心模块

### `agent_framework/agent/service.py`

服务编排层，负责：

- 接收 `AgentRequest`
- 调用路由器生成 `RouteDecision`
- 注入系统 prompt、领域协议和请求上下文
- 调用 LangGraph agent
- 返回 `AgentResponse` 和 `AgentTrace`

未来 Web API、IM Bot、桌面端都应该复用这一层。

### `agent_framework/routing`

路由层负责判断本轮对话应该使用哪个 skill。

当前 `KeywordSkillRouter` 返回结构化 `RouteDecision`，包含：

- `skill`
- `confidence`
- `reason`
- `matched_signals`
- `required_capabilities`
- `clarification_focus`

路由器现在支持传入 thread context。若当前会话已有 `travel_brief`，后续短句补充、地点补充、偏好确认和授权推荐会继续路由到 `business_travel_advisor`，避免多轮商旅任务退回通用问答。

下一步可以升级为 LLM router 或 hybrid router，但返回结构应保持稳定。

### `agent_framework/skills`

Skill 是一组面向任务的行为策略。

当前内置：

- `general_assistant`
- `research_assistant`
- `business_travel_advisor`
- `solution_architect`

`business_travel_advisor` 是当前产品主线 skill，负责 Phase 1 商旅交流和推荐。

### `agent_framework/domains/business_travel.py`

商旅领域协议，定义 Phase 1 必须收集的信息和推荐输出格式。

当前已实现第一阶段商旅工作记忆：

- `TravelBrief`: 结构化记录出发地、目的地、日期、到达时限、预算、偏好、风险等字段。
- `TravelBriefAssessment`: 评估缺失字段、推荐就绪度和最多 3 个建议追问。
- `build_travel_context`: 将用户新输入和已有 thread context 合并，形成可注入 prompt 的商旅上下文。
- 多轮补充：支持把“在陆家嘴上海中心大厦”“都可以，你推荐个最好的”这类后续输入合并进同一份 `TravelBrief`。
- `RecommendationBrief`: 根据 `TravelBrief` 生成结构化推荐简报，包含最佳方案、交通策略、酒店策略、时间线、风险、待核验项、下一步动作和备选方案。

优先收集：

- 出发地和目的地
- 出行日期和时间窗口
- 会议、到达、返程等硬约束
- 预算、差标和报销要求
- 交通、酒店和舒适度偏好
- 风险容忍度

### `agent_framework/core/capabilities.py`

框架能力注册表。

当前 ready 能力：

- `dialogue`
- `web_search`
- `realtime_map`
- `advisor`
- `planner`

当前 reserved 能力：

- `executor`

这表示 Phase 1 可以做推荐和计划，但 Phase 2 的自动执行能力仍未开放。

### `agent_framework/providers/amap.py`

高德地图只读数据 provider，负责：

- 地址/POI 解析
- 两点通勤路线摘要
- 业务地点周边酒店 POI
- 业务地点周边餐饮 POI

该 provider 直接基于 `requests` 调用高德 Web 服务 API，不依赖 `realtime_api/` 参考目录，也不会触发机票/火车票爬虫相关依赖。只有设置 `AMAP_API_KEY` 后，相关工具才会注册进默认 ToolRegistry。

### `agent_framework/tools`

工具注册层，当前接入 Tavily 搜索和高德地图只读工具。

已接入的高德地图工具：

- `amap_location_lookup`
- `amap_route_summary`
- `amap_hotel_search`
- `amap_restaurant_search`

后续接入机票、酒店、日历、审批、报销等 API 时，应先扩展工具元信息：

- 是否需要用户授权
- 是否有副作用
- 输入 schema
- 输出 schema
- 超时和重试
- 审计日志

### `agent_framework/prompts/system.py`

系统提示词集中管理。

它会注入：

- 当前日期
- 产品阶段边界
- 工作原则
- capability 列表
- 当前 skill
- route decision
- request context
- domain protocol
- tool 列表

## Phase 1 推荐演进顺序

1. 已完成：强化商旅信息抽取，维护结构化 `TravelBrief`。
2. 已完成：增加推荐结果 schema，方便前端展示和后续 API 执行。
3. 已完成：接入高德地图只读 API，用于地址、路线、酒店和餐饮 POI 核验。
4. 下一步：接入实时航班/火车/酒店价格/天气等只读 API。
5. 增加 golden tests，评估路由、澄清问题和推荐质量。
6. 再进入 Phase 2 执行型工具，加入授权、审计和回滚。

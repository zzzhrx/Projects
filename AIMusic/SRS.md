# 软件需求规格说明书（SRS）

## 古韵AI — 古风音乐创作工坊

**文档版本**: V1.0  
**编制日期**: 2026-05-13  
**标准依据**: IEEE 830-1998  

---

## 修订记录

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|---------|------|
| V1.0 | 2026-05-13 | 初始版本，完整SRS文档 | 古韵AI项目组 |

---

## 目录

1. 项目概述
2. 功能需求
3. 非功能需求
4. 用户界面设计规范
5. 数据需求
6. 系统架构概述
7. 接口需求
8. 验收标准
9. 项目约束条件
10. 附录

---

## 1. 项目概述

### 1.1 背景

随着人工智能技术在音乐创作领域的广泛应用，专业音乐人对AI辅助创作工具的需求日益增长。当前市面上的AI音乐工具多面向普通用户，缺乏面向专业音乐人的精细控制能力，尤其在古风音乐这一细分领域，缺少能够兼顾专业性与创作效率的工具。专业音乐人需要一种能够精确控制创作过程、支持人工干预修改、并产出专业格式文件的工具。

### 1.2 目标

本项目旨在开发一款面向专业音乐人的AI古风音乐创作工具——"古韵AI"，实现以下核心目标：

1. **四步闭环创作流程**：提示词优化 → 歌词生成 → 曲谱生成 → MIDI导出，每步均支持AI辅助与人工修改的闭环协作
2. **双模型智能分工**：DeepSeek（Pro/Flash）负责创意性文本任务，千问负责结构化专业输出，根据任务特性自动路由
3. **提示词全链路可追溯**：所有步骤的提示词（原始输入、AI优化、人工修改）均完整记录，支持版本对比与回溯
4. **即时音频感知**：曲谱生成后立即可视化渲染五线谱并播放音频，无需等待额外处理
5. **专业格式输出**：支持LRC歌词文件、ABC记谱法曲谱、标准MIDI文件等专业格式导出

### 1.3 范围

**包含范围**：
- 四步创作工作流的完整实现
- DeepSeek Pro/Flash + 千问双模型AI集成
- 提示词版本历史管理系统
- ABC记谱法曲谱渲染与即时播放
- LRC歌词文件生成与导出
- MIDI文件生成与分轨导出
- Windows可执行文件打包
- 古风主题用户界面

**不包含范围**：
- 多用户账户系统和权限管理
- 在线协作功能
- 实时录音功能
- 音频混音与后期处理
- 移动端适配
- macOS/Linux版本

### 1.4 术语与缩写

| 术语/缩写 | 定义 |
|-----------|------|
| ABC记谱法 | 一种基于文本的音乐记谱格式，广泛用于民间音乐和在线音乐交流 |
| LRC | 带有时间戳的歌词文件格式，格式为`[mm:ss.xx]歌词文本` |
| MIDI | 乐器数字接口，一种描述音乐演奏信息的标准数字协议 |
| DeepSeek Pro | DeepSeek公司的高级语言模型(deepseek-chat)，擅长中文创意写作 |
| DeepSeek Flash | DeepSeek公司的快速响应模型，适用于轻量级交互场景 |
| 千问(qwen) | 阿里云通义千问大语言模型(qwen-plus)，擅长结构化专业输出 |
| 五声音阶 | 中国传统音乐音阶体系：宫、商、角、徵、羽 |
| SoundFont | 一种包含乐器音色采样数据的文件格式 |
| SRS | 软件需求规格说明书(Software Requirements Specification) |

---

## 2. 功能需求

### 2.1 系统总体功能模块

系统由以下核心功能模块组成：

| 模块编号 | 模块名称 | 描述 |
|---------|---------|------|
| M1 | 提示词优化模块 | 输入、AI优化、人工修改创作提示词 |
| M2 | 歌词生成模块 | AI生成歌词、人工编辑、LRC文件导出 |
| M3 | 曲谱生成模块 | AI生成曲谱、五线谱渲染、即时播放 |
| M4 | MIDI导出模块 | MIDI文件生成、预览播放、分轨下载 |
| M5 | 提示词版本管理模块 | 版本记录、对比、恢复、导出 |
| M6 | AI模型管理模块 | API Key配置、模型切换、验证 |
| M7 | 系统设置模块 | 参数配置、环境管理 |

### 2.2 M1 — 提示词优化模块

#### 2.2.1 功能描述

用户输入古风音乐创作提示词，系统调用DeepSeek Pro进行专业化优化，用户可对优化结果进行修改，最终确认锁定提示词。

#### 2.2.2 功能需求

| 需求编号 | 需求名称 | 优先级 | 描述 |
|---------|---------|-------|------|
| FR-1.1 | 提示词输入 | 高 | 系统应提供文本输入框，支持用户输入原始古风音乐创作提示词，包括但不限于主题、风格、情感、乐器偏好等描述 |
| FR-1.2 | AI优化提示词 | 高 | 系统应提供"AI优化"按钮，点击后调用DeepSeek Pro API，将用户原始提示词优化为专业古风音乐创作提示词，优化内容包括：补充古风音乐专业术语（宫调式、羽调式、五声音阶等）、明确音乐结构（前奏-主歌-副歌-间奏-尾奏）、细化情感层次和意境描述、指定节奏特征、描述配器建议 |
| FR-1.3 | 优化结果展示与编辑 | 高 | 系统应展示AI优化后的提示词，并提供可编辑的文本区域，允许用户手动修改AI优化结果 |
| FR-1.4 | 快速润色 | 中 | 系统应提供"快速润色"按钮，调用DeepSeek Flash API，对当前提示词进行小幅快速调整建议，响应时间应显著快于完整AI优化 |
| FR-1.5 | 确认提示词 | 高 | 系统应提供"确认提示词"按钮，点击后锁定当前提示词作为最终版本，并自动进入Step 2 |
| FR-1.6 | 原始提示词记录 | 高 | 用户首次输入提示词时，系统应自动记录为`original`类型版本 |
| FR-1.7 | AI优化结果记录 | 高 | AI返回优化结果时，系统应自动记录为`ai_optimized`类型版本 |
| FR-1.8 | 人工修改记录 | 高 | 用户修改并确认提示词时，系统应自动记录为`human_modified`类型版本 |

#### 2.2.3 输入/输出

- **输入**：用户原始提示词（自由文本，最大长度2000字符）
- **输出**：优化后的专业提示词（可编辑文本）

#### 2.2.4 业务规则

- BR-1.1：AI优化应保持用户原始创作意图，仅做专业化扩展
- BR-1.2：优化后的提示词应包含调式、节奏、结构、情感、配器五个维度的描述
- BR-1.3：用户未输入提示词时，"AI优化"按钮应处于禁用状态
- BR-1.4：确认提示词前，系统应提示用户确认操作不可撤回

### 2.3 M2 — 歌词生成模块

#### 2.3.1 功能描述

基于确认的提示词，系统调用DeepSeek Pro生成古风歌词，用户可编辑歌词内容和时间戳，最终导出为LRC格式文件。

#### 2.3.2 功能需求

| 需求编号 | 需求名称 | 优先级 | 描述 |
|---------|---------|-------|------|
| FR-2.1 | 提示词参考展示 | 高 | 系统应在歌词生成页面以只读方式展示Step 1确认的最终提示词 |
| FR-2.2 | 歌词参数配置 | 中 | 系统应提供歌词结构参数配置，包括段落数选择、押韵偏好设置 |
| FR-2.3 | AI生成歌词 | 高 | 系统应提供"生成歌词"按钮，调用DeepSeek Pro API，基于提示词生成结构化古风歌词，歌词应包含段落标记（如[主歌1][副歌]）和每行时间戳（格式[MM:SS.xx]） |
| FR-2.4 | 歌词编辑 | 高 | 系统应提供歌词编辑器，支持用户逐行修改歌词文本内容 |
| FR-2.5 | 时间轴编辑 | 高 | 系统应为每行歌词提供时间戳输入框，格式为MM:SS.mmm，用户可手动调整每行歌词的起始时间 |
| FR-2.6 | 歌词微调建议 | 中 | 用户编辑歌词时，系统应提供"快速建议"按钮，调用DeepSeek Flash API提供简短修改建议 |
| FR-2.7 | LRC文件导出 | 高 | 系统应提供"保存LRC"按钮，将编辑后的歌词导出为标准LRC格式文件供下载 |
| FR-2.8 | 确认歌词 | 高 | 系统应提供"确认歌词"按钮，锁定最终歌词并进入Step 3 |

#### 2.3.3 输入/输出

- **输入**：最终提示词（来自Step 1）、歌词结构参数
- **输出**：结构化歌词文本、LRC格式文件（.lrc）

#### 2.3.4 业务规则

- BR-2.1：AI生成的歌词必须包含时间戳，格式为`[MM:SS.xx]`
- BR-2.2：歌词结构应遵循：主歌-副歌-主歌-副歌-桥段-副歌的标准流行歌曲结构
- BR-2.3：LRC文件格式应符合业界标准，可被常见音乐播放器识别
- BR-2.4：时间戳必须按时间递增排列，不允许出现时间倒流

#### 2.3.5 LRC文件格式规范

```
[ti:曲名]
[ar:古韵AI]
[al:古风创作]

[主歌1]
[00:00.00]第一行歌词
[00:04.50]第二行歌词

[副歌]
[00:12.00]副歌第一行
[00:16.50]副歌第二行
```

### 2.4 M3 — 曲谱生成模块

#### 2.4.1 功能描述

基于确认的歌词，用户输入曲谱提示词，系统调用千问生成ABC记谱法曲谱（人声轨+乐器轨），支持五线谱可视化渲染和即时音频播放。

#### 2.4.2 功能需求

| 需求编号 | 需求名称 | 优先级 | 描述 |
|---------|---------|-------|------|
| FR-3.1 | 歌词参考展示 | 高 | 系统应在曲谱生成页面以只读方式展示Step 2确认的最终歌词 |
| FR-3.2 | 曲谱提示词输入 | 高 | 系统应提供曲谱提示词输入框，允许用户描述曲风、节奏、情感等音乐要素 |
| FR-3.3 | AI优化曲谱提示词 | 高 | 系统应提供"AI优化曲谱提示词"按钮，调用千问API，将用户描述优化为专业音乐术语指令（调性、拍号、速度、力度、织体类型等） |
| FR-3.4 | 曲谱提示词编辑 | 高 | 系统应提供可编辑区域，允许用户修改AI优化后的曲谱提示词 |
| FR-3.5 | 乐器选择 | 高 | 系统应提供乐器选择功能，支持三种乐器：钢琴、古筝、小提琴（三选一），选中状态应高亮显示 |
| FR-3.6 | AI生成曲谱 | 高 | 系统应提供"生成曲谱"按钮，调用千问API，基于歌词和曲谱提示词生成ABC记谱法格式的曲谱，包含人声音轨和所选乐器伴奏音轨 |
| FR-3.7 | 五线谱渲染 | 高 | 系统应使用abcjs将ABC记谱法渲染为可视化五线谱，支持人声轨和乐器轨分轨显示（Tab切换） |
| FR-3.8 | 即时音频播放 | 高 | 曲谱生成完成后，系统应立即提供音频播放能力，使用Tone.js解析ABC曲谱进行即时播放，无需等待后端音频渲染 |
| FR-3.9 | 播放控制 | 高 | 系统应提供播放控制栏，包括播放/暂停/停止按钮 |
| FR-3.10 | 确认曲谱 | 高 | 系统应提供"确认曲谱"按钮，锁定最终曲谱并进入Step 4 |
| FR-3.11 | 曲谱提示词版本记录 | 高 | 曲谱提示词的原始输入、AI优化、人工修改均应记录到版本历史系统 |

#### 2.4.3 输入/输出

- **输入**：最终歌词（来自Step 2）、曲谱提示词、乐器选择
- **输出**：ABC记谱法曲谱（人声轨+乐器轨）、可视化五线谱、即时音频播放

#### 2.4.4 业务规则

- BR-3.1：曲谱必须使用五声音阶（宫商角徵羽）创作旋律
- BR-3.2：人声音轨必须包含歌词对齐（使用ABC记谱法的w:字段）
- BR-3.3：乐器音轨应使用适合所选乐器的伴奏织体
- BR-3.4：曲谱应标注调性、拍号、速度等基本信息
- BR-3.5：音频播放应在曲谱生成后1秒内可启动（即时播放）

#### 2.4.5 ABC记谱法输出格式规范

```
===人声音轨===
X:1
T:人声旋律
M:4/4
L:1/8
Q:1/4=72
K:C
[ABC记谱法人声旋律]

w:歌词对齐

===钢琴音轨===
X:2
T:钢琴伴奏
M:4/4
L:1/8
Q:1/4=72
K:C
[ABC记谱法钢琴伴奏]
```

### 2.5 M4 — MIDI导出模块

#### 2.5.1 功能描述

将确认的ABC曲谱转换为标准MIDI文件，支持预览播放和分轨下载。

#### 2.5.2 功能需求

| 需求编号 | 需求名称 | 优先级 | 描述 |
|---------|---------|-------|------|
| FR-4.1 | 曲谱摘要展示 | 中 | 系统应展示曲谱摘要信息，包括调性、拍号、速度、乐器等 |
| FR-4.2 | MIDI文件生成 | 高 | 系统应提供"生成MIDI"按钮，使用music21将ABC曲谱转换为标准MIDI文件，人声轨和乐器轨分别映射到不同的MIDI轨道 |
| FR-4.3 | MIDI预览播放 | 高 | 系统应提供MIDI预览播放器，使用midi-player-js播放生成的MIDI文件 |
| FR-4.4 | 分轨下载 | 高 | 系统应提供三种下载选项：仅人声轨MIDI、仅乐器轨MIDI、完整合并MIDI |
| FR-4.5 | MIDI文件下载 | 高 | 系统应提供"下载MIDI"按钮，下载标准.mid格式文件 |

#### 2.5.3 输入/输出

- **输入**：确认的ABC曲谱（人声轨+乐器轨）
- **输出**：标准MIDI文件（.mid）

#### 2.5.4 业务规则

- BR-4.1：MIDI文件应符合标准MIDI格式规范（SMF）
- BR-4.2：人声轨应映射到MIDI轨道0，乐器轨应映射到MIDI轨道1
- BR-4.3：合并MIDI文件应保持两条轨道的时间同步

### 2.6 M5 — 提示词版本管理模块

#### 2.6.1 功能描述

记录所有步骤中提示词的变化历史，支持版本查看、对比、恢复和导出。

#### 2.6.2 功能需求

| 需求编号 | 需求名称 | 优先级 | 描述 |
|---------|---------|-------|------|
| FR-5.1 | 版本自动记录 | 高 | 系统应在以下时机自动记录提示词版本：用户首次输入（original）、AI返回优化结果（ai_optimized）、用户修改并确认（human_modified）、用户从历史恢复（restored） |
| FR-5.2 | 历史面板展示 | 高 | 系统应提供可展开/收起的侧边抽屉式历史面板，按时间倒序列出所有版本 |
| FR-5.3 | 版本类型标识 | 高 | 每个版本应使用彩色标签标识类型：[原始]蓝色、[AI优化]紫色、[人工修改]绿色、[回溯]橙色 |
| FR-5.4 | 版本内容查看 | 高 | 点击版本条目应展开显示该版本的完整提示词内容 |
| FR-5.5 | 版本对比 | 中 | 系统应支持两个版本之间的差异对比，新增内容绿色高亮，删除内容红色高亮 |
| FR-5.6 | 版本恢复 | 高 | 系统应提供"恢复此版本"按钮，将历史版本加载到编辑区，并自动创建restored类型的新版本记录 |
| FR-5.7 | 历史导出 | 中 | 系统应提供"导出全部历史"按钮，将所有版本导出为结构化JSON文件 |
| FR-5.8 | 双重存储 | 高 | 提示词版本应同时存储在前端（localStorage）和后端（SQLite数据库） |

#### 2.6.3 版本数据模型

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | INTEGER | 是 | 自增主键 |
| step | TEXT | 是 | 所属步骤（prompt/score） |
| type | TEXT | 是 | 版本类型（original/ai_optimized/human_modified/restored） |
| content | TEXT | 是 | 提示词完整内容 |
| timestamp | DATETIME | 是 | 创建时间 |
| parent_version_id | INTEGER | 否 | 父版本ID（用于追溯修改链） |
| note | TEXT | 否 | 备注/修改原因 |
| session_id | TEXT | 是 | 会话标识 |

### 2.7 M6 — AI模型管理模块

#### 2.7.1 功能描述

管理AI模型的API Key配置、模型选择和验证。

#### 2.7.2 功能需求

| 需求编号 | 需求名称 | 优先级 | 描述 |
|---------|---------|-------|------|
| FR-6.1 | API Key配置 | 高 | 系统应提供设置弹窗，允许用户输入DeepSeek API Key和千问API Key |
| FR-6.2 | API Key持久化 | 高 | API Key应保存到浏览器localStorage，并同步发送到后端更新运行时配置 |
| FR-6.3 | API Key验证 | 中 | 保存API Key时，系统应验证其有效性 |
| FR-6.4 | 模型自动路由 | 高 | 系统应根据任务类型自动选择AI模型：创意任务→DeepSeek Pro、快速建议→DeepSeek Flash、结构化任务→千问 |
| FR-6.5 | 共用Key机制 | 高 | DeepSeek Pro和DeepSeek Flash应共用同一个DeepSeek API Key |

#### 2.7.3 AI模型分工配置

| 模型 | 模型标识 | API Base URL | 职责 | 调用场景 |
|------|---------|-------------|------|---------|
| DeepSeek Pro | deepseek-chat | https://api.deepseek.com | 高质量创意生成 | Step 1提示词优化、Step 2歌词生成 |
| DeepSeek Flash | deepseek-chat (低token/低温度) | https://api.deepseek.com | 快速轻量建议 | 歌词微调、提示词快速润色 |
| 千问 | qwen-plus | https://dashscope.aliyuncs.com/compatible-mode/v1 | 结构化专业输出 | Step 3曲谱提示词优化、ABC曲谱生成 |

#### 2.7.4 业务规则

- BR-6.1：DeepSeek Flash调用应使用max_tokens=256、temperature=0.3参数以实现快速响应
- BR-6.2：所有AI调用均使用OpenAI兼容API格式
- BR-6.3：API Key不得以明文形式记录到日志或版本历史中
- BR-6.4：API Key未配置时，相关AI功能按钮应禁用并提示用户配置

### 2.8 M7 — 系统设置模块

#### 2.8.1 功能需求

| 需求编号 | 需求名称 | 优先级 | 描述 |
|---------|---------|-------|------|
| FR-7.1 | 设置弹窗 | 高 | 系统应提供设置弹窗，包含API Key配置区域 |
| FR-7.2 | 环境变量支持 | 高 | 后端应支持通过.env文件配置API Key |
| FR-7.3 | 会话管理 | 中 | 系统应为每次创作会话分配唯一session_id |

---

## 3. 非功能需求

### 3.1 性能需求

| 编号 | 需求 | 指标 |
|------|------|------|
| NFR-P1 | AI优化提示词响应时间 | DeepSeek Pro调用应在30秒内返回结果 |
| NFR-P2 | 快速建议响应时间 | DeepSeek Flash调用应在5秒内返回结果 |
| NFR-P3 | 曲谱即时播放延迟 | 曲谱生成后1秒内应可开始播放 |
| NFR-P4 | 五线谱渲染时间 | ABC曲谱渲染为五线谱应在2秒内完成 |
| NFR-P5 | MIDI文件生成时间 | 标准长度曲目（3-5分钟）MIDI生成应在5秒内完成 |
| NFR-P6 | 前端页面加载时间 | 首次加载应在3秒内完成 |
| NFR-P7 | LRC文件导出时间 | 应在1秒内完成文件生成和下载 |

### 3.2 安全性需求

| 编号 | 需求 | 描述 |
|------|------|------|
| NFR-S1 | API Key保护 | API Key不得以明文形式存储在代码仓库中，应通过环境变量或加密存储 |
| NFR-S2 | 输入验证 | 所有用户输入应进行长度限制和内容验证，防止注入攻击 |
| NFR-S3 | CORS配置 | 生产环境应限制CORS允许的来源域名 |
| NFR-S4 | API Key传输 | API Key应通过HTTPS传输，前端到后端使用加密通道 |
| NFR-S5 | 文件路径安全 | 文件下载功能应防止路径遍历攻击 |
| NFR-S6 | Skill安全审查 | 使用外部Skill前必须进行安全审查，确认无安全风险后方可使用 |

### 3.3 可靠性需求

| 编号 | 需求 | 描述 |
|------|------|------|
| NFR-R1 | AI调用容错 | AI API调用失败时，系统应显示明确的错误信息，不应崩溃 |
| NFR-R2 | 数据持久化 | 用户创作数据应持久化到localStorage和SQLite，页面刷新不丢失 |
| NFR-R3 | 状态恢复 | 应用异常退出后，应能恢复到最近的创作状态 |
| NFR-R4 | ABC解析容错 | AI生成的ABC曲谱可能格式不完美，系统应尽力解析而非直接报错 |

### 3.4 兼容性需求

| 编号 | 需求 | 描述 |
|------|------|------|
| NFR-C1 | 操作系统 | 支持Windows 10及以上版本 |
| NFR-C2 | 浏览器 | 开发模式下支持Chrome 90+、Edge 90+ |
| NFR-C3 | 显示分辨率 | 支持最低1366×768分辨率，推荐1920×1080 |
| NFR-C4 | MIDI兼容性 | 生成的MIDI文件应兼容主流DAW软件（Cubase、Logic Pro、FL Studio等） |
| NFR-C5 | LRC兼容性 | 生成的LRC文件应兼容主流音乐播放器 |

### 3.5 可维护性需求

| 编号 | 需求 | 描述 |
|------|------|------|
| NFR-M1 | 代码规范 | 前端代码遵循TypeScript严格模式，后端代码遵循PEP 8规范 |
| NFR-M2 | 模块化设计 | 前后端均采用模块化架构，功能模块间低耦合 |
| NFR-M3 | API文档 | 后端API应提供OpenAPI/Swagger自动文档 |
| NFR-M4 | 配置外部化 | 所有可配置项（API Key、模型名、URL等）应通过配置文件管理 |
| NFR-M5 | 日志记录 | 后端应记录关键操作日志，便于问题排查 |

---

## 4. 用户界面设计规范

### 4.1 整体风格

- **主题**：古风中国风
- **基调**：沉稳典雅，专业工具感

### 4.2 色彩规范

| 色彩名称 | 色值 | CSS变量 | 用途 |
|---------|------|---------|------|
| 深墨色 | #1a1a2e | --color-ink | 主背景色 |
| 金色 | #c9a96e | --color-gold | 标题、点缀、重要按钮 |
| 朱红色 | #c0392b | --color-vermilion | 确认按钮、高亮警告 |
| 宣纸白 | #f5f0e8 | --color-rice | 正文文字、输入框背景 |

### 4.3 布局规范

| 区域 | 规范 |
|------|------|
| 顶部标题栏 | 高度60px，深墨色背景，金色标题文字"古韵AI — 古风音乐创作工坊"，右上角设置按钮 |
| 步骤指示器 | 横向四步：①提示词 → ②歌词 → ③曲谱 → ④MIDI，当前步骤金色高亮，已完成步骤绿色勾选，未到达步骤灰色 |
| 内容区 | 居中卡片式布局，最大宽度1200px，卡片圆角12px，深色半透明背景 |
| 侧边抽屉 | 提示词历史面板从右侧滑出，宽度400px，不遮挡主编辑区 |

### 4.4 组件规范

| 组件 | 规范 |
|------|------|
| 按钮-AI操作 | 金色背景(#c9a96e)，深色文字，圆角8px，hover时亮度提升 |
| 按钮-确认操作 | 朱红色背景(#c0392b)，白色文字，圆角8px |
| 按钮-次要操作 | 透明背景，金色边框，hover时背景微亮 |
| 文本输入框 | 深墨色背景，金色边框(20%透明度)，宣纸白文字，focus时边框亮度提升 |
| 文本编辑区 | 最小高度200px，等宽字体显示歌词/曲谱 |
| Tab切换 | 人声/乐器音轨切换，选中Tab金色下划线 |
| 播放控制栏 | 底部固定，包含播放/暂停/停止按钮，进度条 |

### 4.5 交互规范

| 交互 | 规范 |
|------|------|
| 步骤切换 | 只能前进/后退，不可跳步；前进需确认当前步骤 |
| AI生成中 | 显示加载动画（旋转图标+提示文字），按钮禁用 |
| 错误提示 | 页面顶部红色提示条，3秒后自动消失 |
| 成功提示 | 页面顶部绿色提示条，2秒后自动消失 |
| 历史面板 | 点击"历史"按钮展开，点击遮罩层或关闭按钮收起 |

---

## 5. 数据需求

### 5.1 数据模型

#### 5.1.1 实体关系图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Session    │     │    Prompt    │     │    Lyric     │
│─────────────│     │─────────────│     │─────────────│
│ session_id  │────→│ prompt_text │────→│ lyric_text  │
│ created_at  │     │ step        │     │ lrc_content │
│             │     │ type        │     │ timestamps  │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ↓
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Prompt    │     │    Score     │     │    MIDI      │
│   Version   │     │─────────────│     │─────────────│
│─────────────│     │ vocal_abc   │     │ midi_file   │
│ id          │     │ instr_abc   │     │ midi_url    │
│ step        │     │ instrument  │     │ track_type  │
│ type        │     │ prompt      │     └─────────────┘
│ content     │     └─────────────┘
│ timestamp   │
│ session_id  │
└─────────────┘
```

#### 5.1.2 核心数据实体

**Session（会话）**

| 字段 | 类型 | 描述 |
|------|------|------|
| session_id | STRING(UUID) | 会话唯一标识 |
| created_at | DATETIME | 创建时间 |

**PromptVersion（提示词版本）**

| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 自增主键 |
| step | TEXT | NOT NULL, IN('prompt','score') | 所属步骤 |
| type | TEXT | NOT NULL, IN('original','ai_optimized','human_modified','restored') | 版本类型 |
| content | TEXT | NOT NULL | 提示词完整内容 |
| timestamp | DATETIME | DEFAULT NOW | 创建时间 |
| parent_version_id | INTEGER | FK→prompt_versions.id | 父版本ID |
| note | TEXT | | 备注 |
| session_id | TEXT | NOT NULL | 会话标识 |

**LyricData（歌词数据）**

| 字段 | 类型 | 描述 |
|------|------|------|
| lyrics | TEXT | 原始歌词文本 |
| lrc_content | TEXT | LRC格式歌词 |
| timestamps | ARRAY | 时间戳数组 |

**ScoreData（曲谱数据）**

| 字段 | 类型 | 描述 |
|------|------|------|
| vocal_abc | TEXT | 人声音轨ABC记谱法 |
| instrument_abc | TEXT | 乐器音轨ABC记谱法 |
| instrument | ENUM('钢琴','古筝','小提琴') | 乐器类型 |
| score_prompt | TEXT | 曲谱提示词 |

**MidiData（MIDI数据）**

| 字段 | 类型 | 描述 |
|------|------|------|
| midi_file | BLOB | MIDI文件二进制数据 |
| midi_url | TEXT | MIDI文件下载URL |
| track_type | ENUM('vocal','instrument','merged') | 轨道类型 |

### 5.2 数据字典

#### 5.2.1 前端状态数据（Zustand Store）

| 状态字段 | 类型 | 默认值 | 描述 |
|---------|------|-------|------|
| currentStep | number | 0 | 当前步骤（0-3） |
| sessionId | string | '' | 会话ID |
| originalPrompt | string | '' | 原始提示词 |
| optimizedPrompt | string | '' | AI优化后提示词 |
| finalPrompt | string | '' | 最终确认提示词 |
| promptVersions | PromptVersion[] | [] | 提示词版本历史 |
| generatedLyrics | string | '' | AI生成歌词 |
| lrcContent | string | '' | LRC格式内容 |
| finalLyrics | string | '' | 最终确认歌词 |
| scorePrompt | string | '' | 曲谱提示词 |
| optimizedScorePrompt | string | '' | AI优化后曲谱提示词 |
| selectedInstrument | '钢琴'\|'古筝'\|'小提琴' | '钢琴' | 乐器选择 |
| vocalAbc | string | '' | 人声音轨ABC |
| instrumentAbc | string | '' | 乐器音轨ABC |
| scorePromptVersions | PromptVersion[] | [] | 曲谱提示词版本历史 |
| midiUrl | string | '' | MIDI文件URL |
| loading | boolean | false | 加载状态 |
| error | string\|null | null | 错误信息 |

#### 5.2.2 后端配置数据

| 配置项 | 环境变量 | 默认值 | 描述 |
|-------|---------|-------|------|
| DEEPSEEK_API_KEY | DEEPSEEK_API_KEY | '' | DeepSeek API密钥 |
| DEEPSEEK_PRO_MODEL | - | deepseek-chat | DeepSeek Pro模型名 |
| DEEPSEEK_FLASH_MODEL | - | deepseek-chat | DeepSeek Flash模型名 |
| DEEPSEEK_API_BASE_URL | - | https://api.deepseek.com | DeepSeek API地址 |
| QWEN_API_KEY | QWEN_API_KEY | '' | 千问API密钥 |
| QWEN_MODEL | - | qwen-plus | 千问模型名 |
| QWEN_API_BASE_URL | - | https://dashscope.aliyuncs.com/compatible-mode/v1 | 千问API地址 |
| DATABASE_PATH | DATABASE_PATH | ai_music.db | SQLite数据库路径 |

### 5.3 数据流图

#### 5.3.1 顶层数据流图

```
                    ┌──────────┐
                    │   用户    │
                    └────┬─────┘
                         │ 提示词/歌词/曲谱参数
                         ↓
┌─────────────────────────────────────────────────────────┐
│                     古韵AI系统                           │
│                                                         │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌────────┐ │
│  │ Step1   │──→│ Step2   │──→│ Step3   │──→│ Step4  │ │
│  │提示词优化│   │歌词生成  │   │曲谱生成  │   │MIDI导出│ │
│  └────┬────┘   └────┬────┘   └────┬────┘   └───┬────┘ │
│       │             │             │             │      │
│       ↓             ↓             ↓             ↓      │
│  ┌─────────────────────────────────────────────────┐   │
│  │              提示词版本管理（SQLite）              │   │
│  └─────────────────────────────────────────────────┘   │
│       │             │             │                     │
│       ↓             ↓             ↓                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │DeepSeek  │  │DeepSeek  │  │  千问    │             │
│  │  Pro     │  │  Flash   │  │ (qwen)  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
                         │
                         ↓
              ┌──────────────────┐
              │  输出文件         │
              │  .lrc / .mid     │
              └──────────────────┘
```

#### 5.3.2 Step 1 数据流

```
用户 ──[原始提示词]──→ 前端PromptStep
                           │
                           ├──→ 后端 /api/prompt/optimize
                           │         │
                           │         ├──→ 记录original版本 → SQLite
                           │         ├──→ 调用DeepSeek Pro
                           │         └──→ 记录ai_optimized版本 → SQLite
                           │
                           ├──→ 返回优化后提示词 → 可编辑区域
                           │
                           ├──→ [快速润色] → 后端 /api/prompt/quick-suggest
                           │                    └──→ 调用DeepSeek Flash
                           │
                           └──→ [确认] → 记录human_modified版本 → SQLite
                                       → 传递finalPrompt到Step 2
```

#### 5.3.3 Step 2 数据流

```
前端LyricStep ──[finalPrompt + 参数]──→ 后端 /api/lyric/generate
                                            │
                                            ├──→ 调用DeepSeek Pro（含歌词System Prompt）
                                            └──→ 解析歌词文本 → 生成LRC内容
                                                    │
                                                    ↓
                                        返回 {lyrics, lrc_content}
                                                    │
                                                    ↓
                                    前端歌词编辑器（可修改歌词+时间戳）
                                                    │
                                            [保存LRC] → 后端 /api/lyric/export → 下载.lrc文件
                                            [确认] → 传递finalLyrics到Step 3
```

#### 5.3.4 Step 3 数据流

```
前端ScoreStep ──[曲谱提示词]──→ 后端 /api/score/optimize-prompt
                                     │
                                     ├──→ 记录original版本 → SQLite
                                     ├──→ 调用千问（曲谱提示词优化）
                                     └──→ 记录ai_optimized版本 → SQLite
                                              │
                                              ↓
                                  返回优化后曲谱提示词 → 可编辑区域
                                              │
                    [生成曲谱] → 后端 /api/score/generate
                                     │
                                     ├──→ 调用千问（ABC曲谱生成）
                                     └──→ 返回ABC记谱法（人声+乐器）
                                              │
                                              ↓
                              前端abcjs渲染五线谱 + Tone.js即时播放
                                              │
                                      [确认] → 传递ABC到Step 4
```

#### 5.3.5 Step 4 数据流

```
前端MidiStep ──[ABC曲谱]──→ 后端 /api/midi/generate
                                 │
                                 ├──→ music21解析ABC
                                 ├──→ 转换为MIDI文件
                                 └──→ 保存到output目录 → 返回URL
                                          │
                                          ↓
                              前端midi-player-js预览播放
                                          │
                                  [下载] → 后端 /api/midi/download/{filename}
                                          → 下载.mid文件
```

---

## 6. 系统架构概述

### 6.1 总体架构

系统采用前后端分离架构，通过Electron打包为桌面应用：

```
┌──────────────────────────────────────────────────┐
│                  Electron Shell                   │
│  ┌────────────────────────────────────────────┐  │
│  │           Renderer Process                  │  │
│  │  ┌──────────────────────────────────────┐  │  │
│  │  │     React + TypeScript Frontend       │  │  │
│  │  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌─────┐ │  │  │
│  │  │  │Step1 │ │Step2 │ │Step3 │ │Step4│ │  │  │
│  │  │  └──┬───┘ └──┬───┘ └──┬───┘ └──┬──┘ │  │  │
│  │  │     └────────┴────────┴────────┘     │  │  │
│  │  │              │ HTTP API               │  │  │
│  │  │     ┌────────┴────────┐               │  │  │
│  │  │     │  Zustand Store  │               │  │  │
│  │  │     │  (localStorage) │               │  │  │
│  │  │     └─────────────────┘               │  │  │
│  │  └──────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────┘  │
│                        │ HTTP (localhost:8000)    │
│  ┌─────────────────────┴─────────────────────┐  │
│  │           Main Process                      │  │
│  │  ┌──────────────────────────────────────┐  │  │
│  │  │     Python FastAPI Backend            │  │  │
│  │  │  ┌──────────┐  ┌───────────────────┐ │  │  │
│  │  │  │LLMService│  │  MusicService     │ │  │  │
│  │  │  │DeepSeek  │  │  music21          │ │  │  │
│  │  │  │千问      │  │  ABC→MIDI         │ │  │  │
│  │  │  └──────────┘  └───────────────────┘ │  │  │
│  │  │  ┌──────────┐  ┌───────────────────┐ │  │  │
│  │  │  │SQLite DB │  │  Output Files     │ │  │  │
│  │  │  │版本历史   │  │  .mid / .lrc     │ │  │  │
│  │  │  └──────────┘  └───────────────────┘ │  │  │
│  │  └──────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### 6.2 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 前端框架 | React + TypeScript | React 19, TS 5.x | UI组件开发 |
| 构建工具 | Vite | 8.x | 前端构建与开发服务器 |
| CSS框架 | TailwindCSS | 4.x | 样式系统 |
| 状态管理 | Zustand | 5.x | 全局状态+持久化 |
| 曲谱渲染 | abcjs | 6.x | ABC记谱法→五线谱 |
| 音频播放 | Tone.js | 15.x | Web Audio API封装，即时播放 |
| MIDI预览 | midi-player-js | 2.x | MIDI文件播放 |
| 后端框架 | FastAPI | 0.104+ | REST API服务 |
| AI调用 | OpenAI SDK | 1.6+ | 兼容DeepSeek/千问API |
| 音乐处理 | music21 | 9.1+ | ABC解析、MIDI生成 |
| 数据库 | SQLite (aiosqlite) | - | 版本历史持久化 |
| 桌面打包 | Electron | 33.x | Windows桌面应用 |
| 后端打包 | PyInstaller | - | Python→exe |

### 6.3 目录结构

```
g:\cunchu\大学\作业\AI音乐\
├── frontend/                         # React前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── step1/PromptStep.tsx
│   │   │   ├── step2/LyricStep.tsx
│   │   │   ├── step3/ScoreStep.tsx
│   │   │   ├── step3/ScoreDisplay.tsx
│   │   │   ├── step3/AudioPlayer.tsx
│   │   │   ├── step4/MidiStep.tsx
│   │   │   ├── common/PromptHistoryDrawer.tsx
│   │   │   ├── settings/SettingsModal.tsx
│   │   │   └── layout/
│   │   │       ├── AppLayout.tsx
│   │   │       └── StepIndicator.tsx
│   │   ├── services/api.ts
│   │   ├── store/musicStore.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── backend/                          # Python后端
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── routers/
│   │   │   ├── prompt.py
│   │   │   ├── lyric.py
│   │   │   ├── score.py
│   │   │   └── midi.py
│   │   ├── services/
│   │   │   ├── llm_service.py
│   │   │   ├── music_service.py
│   │   │   └── audio_service.py
│   │   ├── models/schemas.py
│   │   └── utils/lrc_utils.py
│   ├── output/
│   ├── requirements.txt
│   └── gu-yun-backend.spec
├── electron/                         # Electron打包
│   ├── main.js
│   └── preload.js
├── package.json                      # 项目根配置
└── .env.example                      # 环境变量示例
```

---

## 7. 接口需求

### 7.1 内部接口（前后端通信）

所有接口基于HTTP RESTful风格，基础路径为`/api`，请求/响应格式为JSON。

#### 7.1.1 提示词相关接口

| 接口 | 方法 | 路径 | 请求体 | 响应体 | 描述 |
|------|------|------|--------|--------|------|
| 提示词优化 | POST | /api/prompt/optimize | {prompt, step, session_id?} | {optimized_prompt, model, session_id} | 调用DeepSeek Pro优化提示词 |
| 快速建议 | POST | /api/prompt/quick-suggest | {text, context?} | {suggestion} | 调用DeepSeek Flash快速建议 |
| 版本历史 | GET | /api/prompt/history/{session_id} | - | {versions[]} | 获取提示词版本历史 |
| 保存人工修改 | POST | /api/prompt/history/save | {step, content, session_id, note?} | {status} | 记录人工修改版本 |

#### 7.1.2 歌词相关接口

| 接口 | 方法 | 路径 | 请求体 | 响应体 | 描述 |
|------|------|------|--------|--------|------|
| 生成歌词 | POST | /api/lyric/generate | {prompt, style?, session_id?} | {lyrics, lrc_content, model, session_id} | 调用DeepSeek Pro生成歌词 |
| 导出LRC | POST | /api/lyric/export | {lrc_content, filename?} | text/plain (文件下载) | 下载LRC文件 |

#### 7.1.3 曲谱相关接口

| 接口 | 方法 | 路径 | 请求体 | 响应体 | 描述 |
|------|------|------|--------|--------|------|
| 优化曲谱提示词 | POST | /api/score/optimize-prompt | {prompt, session_id?} | {optimized_prompt, session_id} | 调用千问优化曲谱提示词 |
| 生成曲谱 | POST | /api/score/generate | {lyrics, style?, session_id?} | {abc_notation, model, session_id} | 调用千问生成ABC曲谱 |
| 渲染音频 | POST | /api/score/render-audio | {abc_notation} | {status, size} | ABC→MIDI数据 |
| 曲谱提示词历史 | GET | /api/score/prompt/history | session_id (query) | {versions[]} | 曲谱提示词版本历史 |

#### 7.1.4 MIDI相关接口

| 接口 | 方法 | 路径 | 请求体 | 响应体 | 描述 |
|------|------|------|--------|--------|------|
| 生成MIDI | POST | /api/midi/generate | {abc_notation, session_id?} | {midi_url, filename} | ABC→MIDI文件 |
| 下载MIDI | GET | /api/midi/download/{filename} | - | audio/midi (文件下载) | 下载MIDI文件 |

#### 7.1.5 设置相关接口

| 接口 | 方法 | 路径 | 请求体 | 响应体 | 描述 |
|------|------|------|--------|--------|------|
| 更新API Key | POST | /api/settings/keys | {deepseek_api_key?, qwen_api_key?} | {status} | 更新AI模型API Key |
| 查询Key状态 | GET | /api/settings/keys/status | - | {deepseek_configured, qwen_configured} | 查询API Key配置状态 |

### 7.2 外部接口

#### 7.2.1 DeepSeek API

| 项目 | 值 |
|------|------|
| API Base URL | https://api.deepseek.com |
| 协议 | HTTPS, OpenAI兼容格式 |
| 认证方式 | Bearer Token (API Key) |
| Pro模型 | deepseek-chat |
| Flash参数 | max_tokens=256, temperature=0.3 |
| 调用场景 | 提示词优化(Pro)、歌词生成(Pro)、快速建议(Flash) |

#### 7.2.2 千问API

| 项目 | 值 |
|------|------|
| API Base URL | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| 协议 | HTTPS, OpenAI兼容格式 |
| 认证方式 | Bearer Token (API Key) |
| 模型 | qwen-plus |
| 调用场景 | 曲谱提示词优化、ABC曲谱生成 |

---

## 8. 验收标准

### 8.1 功能验收标准

| 编号 | 验收项 | 验收标准 | 验收方法 |
|------|-------|---------|---------|
| AC-F1 | 提示词优化 | 输入任意古风音乐描述，AI返回包含调式、节奏、结构、情感、配器五个维度的专业提示词 | 手动测试10组不同输入 |
| AC-F2 | 歌词生成 | 基于提示词生成包含段落标记和时间戳的古风歌词，LRC文件可被标准播放器识别 | 生成歌词并导入播放器验证 |
| AC-F3 | 曲谱生成 | 基于歌词生成包含人声轨和乐器轨的ABC曲谱，abcjs可正确渲染五线谱 | 生成曲谱并验证渲染结果 |
| AC-F4 | 即时播放 | 曲谱生成后1秒内可点击播放，Tone.js输出音频 | 计时测试 |
| AC-F5 | MIDI导出 | 生成的MIDI文件可在Cubase/FL Studio等DAW中正常打开，双轨道正确 | DAW导入验证 |
| AC-F6 | 提示词版本记录 | 每步操作均自动记录版本，历史面板可查看、对比、恢复 | 操作后检查SQLite记录 |
| AC-F7 | 乐器选择 | 选择不同乐器生成曲谱，伴奏音轨应有对应差异 | 分别选择三种乐器测试 |
| AC-F8 | 分轨下载 | 可分别下载人声轨、乐器轨、合并MIDI文件 | 下载并验证各文件 |

### 8.2 非功能验收标准

| 编号 | 验收项 | 验收标准 |
|------|-------|---------|
| AC-N1 | 前端构建 | `npm run build`无错误通过 |
| AC-N2 | 后端启动 | `uvicorn app.main:app`正常启动，API文档可访问 |
| AC-N3 | API Key安全 | API Key不出现在代码仓库、日志、版本历史中 |
| AC-N4 | 数据持久化 | 页面刷新后创作状态不丢失 |
| AC-N5 | 错误处理 | AI调用失败时显示明确错误信息，不崩溃 |
| AC-N6 | exe打包 | `npm run build`生成可安装的Windows exe文件 |

---

## 9. 项目约束条件

### 9.1 技术约束

| 编号 | 约束 | 描述 |
|------|------|------|
| TC-1 | 操作系统 | 仅支持Windows 10及以上 |
| TC-2 | AI模型依赖 | 系统功能依赖DeepSeek和千问API的可用性，需用户自行获取API Key |
| TC-3 | 网络要求 | AI调用需联网，离线状态仅可使用已生成的本地数据 |
| TC-4 | Python版本 | 后端需Python 3.9+ |
| TC-5 | Node.js版本 | 前端需Node.js 18+ |

### 9.2 业务约束

| 编号 | 约束 | 描述 |
|------|------|------|
| BC-1 | 单用户模式 | 系统为单机桌面应用，不支持多用户并发 |
| BC-2 | AI生成质量 | AI生成的歌词和曲谱质量受模型能力限制，需人工审核修改 |
| BC-3 | 乐器限制 | 当前仅支持钢琴、古筝、小提琴三种乐器 |
| BC-4 | 曲谱格式 | 曲谱使用ABC记谱法，不支持直接导入MusicXML等其他格式 |

### 9.3 开发约束

| 编号 | 约束 | 描述 |
|------|------|------|
| DC-1 | 外部Skill使用 | 使用外部Skill前必须进行安全审查 |
| DC-2 | 代码注释 | 代码注释使用中文 |
| DC-3 | API兼容 | AI调用统一使用OpenAI兼容格式 |

---

## 10. 附录

### 10.1 术语表

| 术语 | 定义 |
|------|------|
| ABC记谱法 | ABC Notation，一种基于ASCII文本的音乐记谱语言，由Chris Walshaw开发，广泛用于民间音乐的记录和交流 |
| LRC格式 | Lyrics File Format，一种包含时间同步信息的歌词文件格式，文件扩展名为.lrc |
| MIDI | Musical Instrument Digital Interface，乐器数字接口，一种连接电子乐器的通信协议和文件格式 |
| DAW | Digital Audio Workstation，数字音频工作站，如Cubase、Logic Pro、FL Studio等 |
| 五声音阶 | Pentatonic Scale，由五个音构成的音阶，中国传统音乐使用宫、商、角、徵、羽 |
| 宫调式 | 以"宫"音为主音的中国传统调式 |
| 羽调式 | 以"羽"音为主音的中国传统调式 |
| 伴奏织体 | Accompaniment Texture，伴奏的音乐组织方式，如柱式和弦、分解和弦、琶音等 |
| SoundFont | 一种包含乐器音色采样数据的文件格式，用于MIDI合成器 |
| CORS | Cross-Origin Resource Sharing，跨域资源共享，一种浏览器安全机制 |
| PyInstaller | 将Python应用打包为独立可执行文件的工具 |
| Electron | 使用Web技术构建桌面应用的框架 |

### 10.2 参考资料

| 编号 | 参考资料 | 描述 |
|------|---------|------|
| REF-1 | IEEE 830-1998 | IEEE Recommended Practice for Software Requirements Specifications |
| REF-2 | ABC Notation Standard | ABC记谱法官方标准规范 |
| REF-3 | MIDI 1.0 Specification | MIDI标准规范 |
| REF-4 | DeepSeek API Documentation | DeepSeek API官方文档 |
| REF-5 | 通义千问API Documentation | 阿里云千问API官方文档 |
| REF-6 | music21 Documentation | music21音乐分析库文档 |
| REF-7 | abcjs Documentation | abcjs曲谱渲染库文档 |
| REF-8 | Tone.js Documentation | Tone.js音频框架文档 |

### 10.3 LRC格式规范参考

```
[ti:标题]
[ar:艺术家]
[al:专辑]
[by:编辑者]
[offset:时间偏移量(毫秒)]

[mm:ss.xx]歌词行1
[mm:ss.xx]歌词行2
```

时间戳格式说明：
- mm：分钟（两位数）
- ss：秒（两位数）
- xx：百分之一秒（两位数）或毫秒（三位数）

### 10.4 ABC记谱法格式参考

```
X:1                    序号
T:曲名                 标题
M:4/4                  拍号
L:1/8                  默认音符长度
Q:1/4=72               速度
K:C                    调性
CDEFGAB                音符（C大调）
z                      休止符
|                      小节线
w:歌词                 歌词对齐
```

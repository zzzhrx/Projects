# 古韵AI — 古风音乐创作工坊

AI 辅助古风音乐创作桌面工具，将创作过程拆解为**提示词优化 → 歌词生成 → 曲谱生成 → MIDI导出**四个步骤，支持人工编辑与 AI 协作。

## 功能特性

- **四步串行创作流程**：提示词 → 歌词 → 曲谱 → MIDI，每步可确认后进入下一步
- **双 AI 模型协作**：DeepSeek 负责创意文本（提示词/歌词），千问负责结构化输出（ABC 曲谱）
- **歌词编辑与 LRC 导出**：逐行编辑歌词与时间轴，导出标准 LRC 歌词文件
- **五线谱渲染**：基于 abcjs 实时渲染人声+乐器双音轨五线谱
- **即时音频预览**：步骤3 用 Tone.js 即时播放曲谱，带进度条与时间显示
- **分轨 MIDI 导出**：支持仅人声/仅乐器/完整合并三种导出，带歌词元数据嵌入
- **提示词版本历史**：自动记录每步提示词，支持查看、恢复、导出 JSON
- **乐器选择**：钢琴/古筝/小提琴，MIDI 中自动设置对应 GM 音色

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Vite 8 + TailwindCSS 4 + Zustand 5 |
| 后端 | Python FastAPI + SQLite (aiosqlite) |
| AI 模型 | DeepSeek (deepseek-chat) + 千问 (qwen-plus) |
| 音乐引擎 | abcjs 6.6 (五线谱) + Tone.js 15.1 (音频播放) + music21 9.x (MIDI 转换) + @tonejs/midi (MIDI 解析) |
| 桌面壳 | Electron 33 (Windows exe 打包) |

## 环境要求

- **Python**: 3.10+ （推荐 conda 管理环境）
- **Node.js**: 18+
- **macOS / Windows / Linux**

## 安装

```bash
# 1. 克隆项目
cd AI音乐

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt

# 3. 安装前端依赖
cd ../frontend
npm install

# 4. 配置 API Key（见下方）
cp ../.env.example backend/.env
# 编辑 backend/.env，填入你的 API Key
```

## 配置 API Key

编辑 `backend/.env`：

```env
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
QWEN_API_KEY=你的千问_API_Key
```

也可以启动后在 UI 设置弹窗中输入（点击右上角齿轮图标）。

> **获取 API Key**:
> - DeepSeek: https://platform.deepseek.com/api_keys
> - 千问 (Qwen): https://dashscope.aliyun.com/

## 启动

```bash
# 终端1：启动后端
cd backend
python -m uvicorn app.main:app --reload --port 8000

# 终端2：启动前端
cd frontend
npx vite --port 5173
```

打开浏览器访问 `http://localhost:5173`

---

## 用户操作指南

### 界面概览

页面顶部有**四步指示器**，当前步骤金色高亮，已完成步骤绿色勾选。右上角齿轮图标打开 **API Key 设置**。

---

### 步骤1：提示词创作

> 把你的音乐想法变成专业的创作指令

**操作：**

1. 在文本区输入古风音乐描述，例如：
   > 月下独酌，清风拂柳，婉约忧伤。以古筝为主旋律，笛声点缀，描绘江南秋夜的寂寥画面。

2. 点击 **「AI 优化」**——DeepSeek Pro 将你的描述扩展为包含调式、节奏、结构、情感层次、配器建议的专业提示词

3. 点击 **「快速润色」**——DeepSeek Flash 提供简短修改建议（速度快）

4. 在优化结果区域**手动编辑**，调整到满意

5. 点击 **「确认提示词」** 进入下一步

**提示词历史：** 右侧面板可查看所有版本，点击展开后可以「恢复此版本」或「导出历史」为 JSON 文件。

---

### 步骤2：歌词生成

> AI 生成带时间戳的结构化古风歌词，逐行编辑

**操作：**

1. 选择**段落数**（1~4段）和**押韵偏好**（自动/ang韵/an韵/ing韵/ou韵）

2. 点击 **「生成歌词」**——DeepSeek Pro 生成带 LRC 时间戳的歌词

3. **编辑歌词**：在歌词编辑器中逐行修改，左侧行号辅助定位

4. **「快速建议」**：AI 提供歌词改进建议

5. **编辑时间轴**：下方时间轴面板可逐个调整每行时间戳（格式 `MM:SS.mmm`）

6. **「保存 LRC」**：导出标准 LRC 歌词文件，可导入 DAW 或其他音乐软件

7. 点击 **「确认歌词」** 进入下一步

---

### 步骤3：曲谱生成

> AI 生成五线谱，支持试听播放

**操作：**

1. 在**曲谱提示词**区域描述想要的和声风格、节奏特征（也可先用「AI优化曲谱提示词」润色）

2. **选择乐器**：钢琴、古筝、小提琴（影响 MIDI 导出音色）

3. 点击 **「生成曲谱」**——千问模型生成 ABC 记谱法曲谱

4. **五线谱渲染**：右侧显示五线谱，可通过「人声音轨/乐器音轨」标签切换查看

5. **播放试听**：点击 ▶ 播放当前音轨，有进度条和时间显示（`0:00 / 0:30`）

6. **「曲谱提示词历史」**：底部按钮可查看历史版本并恢复

7. 点击 **「确认曲谱」** 进入最后一步

> **提示**：如果生成的旋律听起来重复单调，尝试在曲谱提示词中给出更具体的风格描述，如"旋律要有起承转合，副歌处上行大跳"。

---

### 步骤4：MIDI 导出

> 生成标准 MIDI 文件，支持分轨下载和内置播放

**操作：**

1. **选择导出类型**：
   - **仅人声**：只含人声旋律轨，带歌词元数据——可导入其他配唱软件
   - **仅乐器**：只含伴奏轨
   - **完整合并**：人声 + 乐器双轨

2. 点击 **「生成 MIDI」**

3. **预览播放**：点击 ▶ 播放 MIDI，蓝色进度条推进

   - 人声轨用 triangle 波形（更明亮），伴奏轨用 sine 波形（更柔和）
   - 播放时**歌词字幕**实时显示
   - 下方滚动面板显示全部歌词，当前句金色高亮

4. **「下载 MIDI」**——保存 `.mid` 文件到本地

5. 点击 **「重新创作」** 开始新一轮创作

---

## MIDI 文件结构

生成的 MIDI 文件包含：

| 轨道 | 名称 | GM 音色 | 内容 |
|------|------|---------|------|
| Track 0 | Conductor | — | 速度、拍号 |
| Track 1 | Voice | 53 (Choir Aahs) | 人声旋律 + 歌词元数据 |
| Track 2 | 钢琴/古筝/小提琴 | 0 / 107 / 40 | 伴奏 |

> **关于歌词**：歌词以 MIDI Lyric Meta-Event (FF 05) 格式嵌入 Track 1，可在 Cubase、Logic Pro、FL Studio 等 DAW 中查看。简单 MIDI 播放器可能不显示歌词。

---

## 项目结构

```
AI音乐/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # .env 加载
│   │   ├── database.py          # SQLite 数据库
│   │   ├── models/schemas.py    # Pydantic 模型
│   │   ├── routers/
│   │   │   ├── prompt.py        # 提示词 API
│   │   │   ├── lyric.py         # 歌词 API
│   │   │   ├── score.py         # 曲谱 API
│   │   │   └── midi.py          # MIDI API
│   │   ├── services/
│   │   │   ├── llm_service.py   # AI 模型调用
│   │   │   ├── music_service.py # music21 音乐处理
│   │   │   └── audio_service.py # 音频渲染
│   │   └── utils/lrc_utils.py   # LRC 解析/生成
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── step1/PromptStep.tsx
│       │   ├── step2/LyricStep.tsx
│       │   ├── step3/ScoreStep.tsx  ScoreDisplay.tsx  AudioPlayer.tsx
│       │   ├── step4/MidiStep.tsx
│       │   ├── common/PromptHistoryDrawer.tsx
│       │   ├── settings/SettingsModal.tsx
│       │   └── layout/AppLayout.tsx  StepIndicator.tsx
│       ├── services/api.ts       # API 封装
│       ├── store/musicStore.ts   # Zustand 全局状态
│       └── App.tsx
├── electron/                     # Electron 桌面壳
├── .env.example
└── SRS.md                        # 需求规格说明书
```

## 常见问题

**Q: 提示"请先配置 API Key"**
A: 点击右上角齿轮图标，输入 DeepSeek 和千问的 API Key，点击保存。

**Q: 生成的旋律太单调**
A: 在步骤3的「曲谱提示词」中给出更详细的风格描述，如"每句歌词配4小节不同的旋律，副歌要有情绪爆发，使用附点节奏增加律动感"。

**Q: MIDI 播放没有声音**
A: 前端播放需要浏览器支持 Web Audio API（Chrome/Edge/Firefox 均可）。下载的 `.mid` 文件建议用 VLC 或 DAW 打开。

**Q: 为什么听不到人唱歌词**
A: MIDI 本身无法合成人声演唱。本项目提供的是旋律轨（可听）和歌词元数据（可看）。需要将 MIDI 导入 DAW 或配唱软件（如 Synthesizer V、Vocaloid）来合成实际人声。

**Q: 如何只用人声旋律**
A: 步骤4 选择「仅人声」→「生成 MIDI」→「下载 MIDI」，得到纯净的人声旋律轨（带歌词元数据），可直接导入配唱软件。

**Q: 后端启动报错**
A: 确保已安装所有 Python 依赖：`pip install -r requirements.txt`，并已激活正确的 conda 环境。

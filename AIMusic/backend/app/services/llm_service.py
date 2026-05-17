from openai import AsyncOpenAI
from app.config import settings


class LLMService:
    def __init__(self):
        self._deepseek_key = settings.DEEPSEEK_API_KEY
        self._qwen_key = settings.QWEN_API_KEY
        self.deepseek_client = AsyncOpenAI(
            api_key=self._deepseek_key,
            base_url=settings.DEEPSEEK_API_BASE_URL,
        )
        self.qwen_client = AsyncOpenAI(
            api_key=self._qwen_key,
            base_url=settings.QWEN_API_BASE_URL,
        )

    def update_keys(self, deepseek_key: str = None, qwen_key: str = None):
        if deepseek_key is not None:
            self._deepseek_key = deepseek_key
            self.deepseek_client = AsyncOpenAI(
                api_key=self._deepseek_key,
                base_url=settings.DEEPSEEK_API_BASE_URL,
            )
        if qwen_key is not None:
            self._qwen_key = qwen_key
            self.qwen_client = AsyncOpenAI(
                api_key=self._qwen_key,
                base_url=settings.QWEN_API_BASE_URL,
            )

    def _ensure_key(self, provider: str):
        if provider == "deepseek" and not self._deepseek_key:
            raise ValueError("请先在设置中配置 DeepSeek API Key。")
        if provider == "qwen" and not self._qwen_key:
            raise ValueError("请先在设置中配置千问 API Key。")

    async def call_deepseek_pro(self, prompt: str, system_prompt: str = "") -> str:
        self._ensure_key("deepseek")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.deepseek_client.chat.completions.create(
            model=settings.DEEPSEEK_PRO_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content

    async def call_deepseek_flash(self, prompt: str, system_prompt: str = "") -> str:
        self._ensure_key("deepseek")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.deepseek_client.chat.completions.create(
            model=settings.DEEPSEEK_FLASH_MODEL,
            messages=messages,
            max_tokens=256,
            temperature=0.3,
        )
        return response.choices[0].message.content

    async def call_qwen(self, prompt: str, system_prompt: str = "") -> str:
        self._ensure_key("qwen")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.qwen_client.chat.completions.create(
            model=settings.QWEN_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content

    async def optimize_prompt(self, user_prompt: str, step: str = "prompt") -> str:
        """使用DeepSeek Pro优化提示词"""
        system_prompt = """你是一位专业的古风音乐创作顾问。你的任务是将用户提供的音乐创作描述优化为专业、精确的创作提示词。
优化要求：
1. 补充古风音乐专业术语（如：宫调式、羽调式、五声音阶等）
2. 明确音乐结构（前奏-主歌-副歌-间奏-尾奏）
3. 细化情感层次和意境描述
4. 指定节奏特征（如：慢板、中板、快板）
5. 描述配器建议（古筝、钢琴、小提琴等）
6. 保持用户原始意图，仅做专业化扩展
请直接输出优化后的提示词，不要解释。"""
        return await self.call_deepseek_pro(user_prompt, system_prompt)

    async def generate_lyrics(
        self,
        prompt: str,
        style: str = "古风",
        paragraph_count: int = 2,
        rhyme_preference: str = "auto",
    ) -> str:
        """使用DeepSeek Pro生成歌词"""
        system_prompt = f"""你是一位古风歌词创作大师。根据提示词创作古风歌词。
要求：
1. 使用{style}风格
2. 歌词结构需要控制在约{paragraph_count}个主要段落内，保留清晰段落标记
3. 每行歌词前标注时间戳，格式：[MM:SS.xx]
4. 使用古风意象和修辞手法
5. 押韵偏好：{rhyme_preference}
6. 在歌词前用[段落标记]标注结构（如[主歌1][副歌]等）

输出格式示例：
[主歌1]
[00:00.00]第一行歌词
[00:04.50]第二行歌词
[副歌]
[00:12.00]副歌第一行
..."""
        return await self.call_deepseek_pro(prompt, system_prompt)

    async def quick_suggest(self, text: str, context: str = "") -> str:
        """使用DeepSeek Flash提供快速建议"""
        system_prompt = """你是音乐创作助手，提供简短的修改建议。只输出建议内容，不超过50字。"""
        full_prompt = f"上下文：{context}\n请对以下内容提供简短修改建议：{text}" if context else f"请对以下内容提供简短修改建议：{text}"
        return await self.call_deepseek_flash(full_prompt, system_prompt)

    async def optimize_score_prompt(self, user_prompt: str) -> str:
        """使用千问优化曲谱提示词"""
        system_prompt = """你是一位专业的音乐理论家和曲谱编排专家。将用户的曲谱描述优化为专业的音乐创作指令。
优化要求：
1. 使用专业音乐术语（调性、拍号、速度、力度等）
2. 明确人声旋律线的特征
3. 指定伴奏织体类型（柱式和弦、分解和弦、琶音等）
4. 标注调式（如C宫调式、D羽调式等五声调式）
5. 描述各乐器的演奏技法和音区
请直接输出优化后的曲谱创作指令。"""
        return await self.call_qwen(user_prompt, system_prompt)

    async def generate_score(self, lyrics: str, score_prompt: str, instrument: str = "钢琴") -> str:
        """使用千问生成ABC记谱法曲谱"""
        system_prompt = f"""你是ABC记谱法专家。只输出ABC曲谱，不要其他文字。

===人声音轨===
X:1
T:人声旋律
M:4/4
L:1/8
Q:1/4=72
K:Dmin
%%staves [1]
V:1 clef=treble name="Vocal"
D4 z2 A,2 D2 | F4 E2 D2 D2 | z8 | z8 |
A,2 D2 F4 E2 | D4 z2 A,2 D2 | F2 G2 A4 F2 | E2 D4 z4 |
A4 A2 G2 F2 | E4 D2 C2 D2 | F4 E2 D4 | z8 |
w:主 歌 第 一 句 歌 词 对 齐* 主 歌 第 二 句* 主 歌 第 三 句 歌 词* 主 歌 第 四 句*
w:副 歌 第 一 句 高 潮* 副 歌 第 二 句* 副 歌 第 三 句 结 尾* 副 歌 第 四 句*

==={instrument}音轨===
X:2
T:{instrument}伴奏
M:4/4
L:1/8
Q:1/4=72
K:Dmin
%%staves [1]
V:1 clef=treble name="{instrument}"
[D4F4A4] z4 [D4F4A4] z2 | [E4G4B4] z4 [E4G4B4] z2 |
[D4F4A4] z4 [G4B4d4] z2 | [C4E4G4] z4 [C4E4G4] z2 |
[D4F4A4] z4 [D4F4A4] z2 | [E4G4B4] z4 [E4G4B4] z2 |
[D4F4A4] z4 [G4B4d4] z2 | [C4E4G4] z4 [C4E4G4] z2 |
[D4F4A4] z4 [D4F4A4] z2 | [A,4C4E4] z4 [A,4C4E4] z2 |
[D4F4A4] z4 [D4F4A4] z2 | [C4E4G4] z4 [C4E4G4] z2 |"""
        full_prompt = f"""请根据以下歌词，创作一首完整的古风歌曲ABC曲谱（人声旋律+{instrument}伴奏）。

歌词：
{lyrics}

曲谱风格：{score_prompt or '古风，五声音阶，慢板'}

要求：
1. 人声旋律必须写满与歌词行数对应的小节数，每句歌词至少配2小节
2. 旋律每小节音符要有变化，节奏要有长有短（不要全是一种节奏）
3. w: 行必须与歌词一一对齐，用 * 分隔每句
4. {instrument}伴奏用方括号和弦记法，如 [CEG] 表示C和弦
5. 伴奏至少要有Dm, Am, Gm, C 四种和弦交替使用，不要一直重复同一个和弦
6. 直接输出ABC曲谱，严格按照上面示例的格式"""
        return await self.call_qwen(full_prompt, system_prompt)


llm_service = LLMService()

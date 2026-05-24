"""Skill discovery + progressive disclosure for ReAct agent.

Directory structure:
    skill/
        skill_xxx/
            SKILL.md   # required, progressive disclosure format
            README.md  # optional

SKILL.md format:
    ---
    name: skill_xxx
    description: 一句话描述
    trigger_keywords: [keyword1, keyword2]  # optional
    ---

    # Skill: xxx

    ## 用途概要
    简要说明（用于快速判断是否需要）

    ## 详细说明
    完整说明（按需加载）

    ## 使用工具
    列出可用的工具或能力

    ## 使用方法
    如何调用此技能
"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SKILL_DIR = Path(__file__).parent.parent.parent / "skill"


class Skill:
    """Single skill with progressive disclosure content."""
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.skill_file = path / "SKILL.md"
        self._summary: Optional[str] = None
        self._detail: Optional[str] = None

    def load(self):
        """Load and parse SKILL.md."""
        if not self.skill_file.exists():
            raise FileNotFoundError(f"SKILL.md not found in {self.path}")

        content = self.skill_file.read_text(encoding="utf-8")
        # Parse frontmatter
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                frontmatter = content[3:end].strip()
                body = content[end + 3:].strip()
                self._parse_frontmatter(frontmatter)
                self._parse_body(body)
            else:
                self._parse_body(content)
        else:
            self._parse_body(content)

    def _parse_frontmatter(self, fm_text: str):
        for line in fm_text.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                setattr(self, key.strip(), val.strip())

    def _parse_body(self, body: str):
        # Progressive disclosure: first section is summary, rest is detail
        parts = body.split("\n## ", 1)
        if len(parts) > 1:
            # First part might have '# Skill: xxx' header
            summary_section = parts[0].replace("# Skill:", "").strip()
            self._summary = summary_section
            self._detail = "\n## ".join(parts[1:])
        else:
            self._summary = body
            self._detail = body

    @property
    def summary(self) -> str:
        if self._summary is None:
            self.load()
        return self._summary or ""

    @property
    def detail(self) -> str:
        if self._detail is None:
            self.load()
        return self._detail or ""

    def match(self, query: str) -> float:
        """Simple keyword matching. Returns 0.0 - 1.0 relevance score."""
        query_lower = query.lower()
        score = 0.0

        # Check trigger_keywords first (highest weight)
        trigger_kw = getattr(self, "trigger_keywords", None)
        if trigger_kw:
            # trigger_kw is stored as a string like "[转换,诗,诗意,词]"
            import ast
            try:
                kw_list = ast.literal_eval(trigger_kw) if isinstance(trigger_kw, str) else trigger_kw
            except (ValueError, SyntaxError):
                # Fallback: strip brackets and split
                cleaned = trigger_kw.strip("[]")
                kw_list = [k.strip() for k in cleaned.split(",")]

            query_lower = query.lower()
            # For CJK queries, also check character-level (Chinese has no word boundaries)
            query_chars = set(query_lower) if not query_lower.isascii() else set()

            for tk in kw_list:
                tk_lower = tk.lower()
                # Multi-char trigger keyword: check if fully contained OR any char matches
                if len(tk_lower) > 1:
                    if tk_lower in query_lower:
                        score += 0.5
                    elif query_chars and any(c in query_chars for c in tk_lower):
                        score += 0.5
                # Single char trigger keyword: check char-level overlap
                elif len(tk_lower) == 1:
                    if tk_lower in query_chars:
                        score += 0.5

        # Check description
        desc = getattr(self, "description", "") or ""
        for kw in query_lower.split():
            if kw in desc.lower():
                score += 0.3

            # Check name (inside loop so every keyword is checked)
            if kw in self.name.lower():
                score += 0.4

            # Check summary (inside loop)
            if kw in self.summary.lower():
                score += 0.2

        return min(score, 1.0)


class SkillManager:
    """Discovers and manages skills from skill/ directory."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills: dict[str, Skill] = {}
            cls._instance._loaded = False
        return cls._instance

    def _ensure_loaded(self):
        if self._loaded:
            return

        skill_dir = SKILL_DIR
        if not skill_dir.exists():
            logger.warning("Skill directory not found: %s", skill_dir)
            self._loaded = True
            return

        for entry in skill_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                try:
                    skill = Skill(entry)
                    skill.load()
                    self._skills[skill.name] = skill
                    logger.info("Loaded skill: %s", skill.name)
                except Exception as e:
                    logger.error("Failed to load skill %s: %s", entry.name, e)

        self._loaded = True
        logger.info("Total skills loaded: %d", len(self._skills))

    def list_skills(self) -> list[Skill]:
        """Return all available skills."""
        self._ensure_loaded()
        return list(self._skills.values())

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a specific skill by name."""
        self._ensure_loaded()
        return self._skills.get(name)

    def find_relevant_skills(self, query: str, threshold: float = 0.3) -> list[tuple[Skill, float]]:
        """Find skills relevant to query, sorted by relevance score."""
        self._ensure_loaded()
        scored = [(s, s.match(query)) for s in self._skills.values()]
        relevant = [(s, score) for s, score in scored if score >= threshold]
        relevant.sort(key=lambda x: x[1], reverse=True)
        return relevant

    def build_skill_context(self, query: str, max_skills: int = 3) -> str:
        """Build progressive disclosure context for relevant skills."""
        relevant = self.find_relevant_skills(query, threshold=0.2)
        if not relevant:
            return ""

        parts = ["[Skills Available]"]
        for skill, score in relevant[:max_skills]:
            parts.append(f"\n=== Skill: {skill.name} ===")
            parts.append(skill.summary)
            # Optionally include detail for high-relevance skills
            if score > 0.5 and skill.detail != skill.summary:
                parts.append("\n[Detail]")
                parts.append(skill.detail)

        return "\n".join(parts)


# Singleton instance
_skill_manager = SkillManager()


def get_skill_manager() -> SkillManager:
    return _skill_manager


def build_skill_context_for_prompt(user_input: str) -> str:
    """Build skill context string to prepend to system prompt."""
    return _skill_manager.build_skill_context(user_input)


if __name__ == "__main__":
    # Test
    sm = get_skill_manager()
    print("Skills:", [s.name for s in sm.list_skills()])
    print("\nContext for '天气':", build_skill_context_for_prompt("北京天气怎么样"))
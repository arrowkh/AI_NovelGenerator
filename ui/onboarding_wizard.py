# ui/onboarding_wizard.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
import shutil
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox

from config_manager import save_config
from tooltips import tooltips
from ui.hover_tooltip import attach_hover_tooltip


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


TEMPLATES_JSON_PATH = _project_root() / "resources" / "templates" / "project_templates.json"
EXAMPLE_PROJECTS_INDEX_PATH = _project_root() / "resources" / "example_projects" / "index.json"
EXAMPLE_PROJECTS_DIR = _project_root() / "resources" / "example_projects"


@dataclass(frozen=True)
class ProjectTemplate:
    """项目模板：用于新手快速创建项目，并应用推荐配置。"""

    template_id: str
    name: str
    category: str
    description: str
    recommended_config: dict[str, Any]
    defaults: dict[str, Any]
    estimate: dict[str, Any]
    highlights: list[str]

    @classmethod
    def load_all(cls) -> list[ProjectTemplate]:
        if TEMPLATES_JSON_PATH.exists():
            try:
                data = json.loads(TEMPLATES_JSON_PATH.read_text(encoding="utf-8"))
                return [cls(**item) for item in data]
            except Exception:
                pass

        return cls.builtin_templates()

    @classmethod
    def builtin_templates(cls) -> list[ProjectTemplate]:
        return [
            cls(
                template_id="standard_webnovel_xuanhuan",
                name="标准网文（玄幻/仙侠）",
                category="玄幻/仙侠",
                description="快速产出、节奏明快、爽点密集，适合连载型网文。",
                recommended_config={
                    "interface_format": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "model_name": "gpt-4o-mini",
                    "temperature": 0.8,
                    "max_tokens": 8192,
                    "timeout": 600,
                },
                defaults={"per_chapter_words": 3000, "planned_chapters": 500, "planned_total_words": 500000},
                estimate={"duration": "2周", "chapters": 500, "cost_usd": 45},
                highlights=["快速生成", "爽点足", "适合长篇连载"],
            ),
            cls(
                template_id="high_quality_romance_modern",
                name="高质量文学（现代/言情）",
                category="现代/言情",
                description="重视人物情感与细节刻画，适合中短篇、精修型作品。",
                recommended_config={
                    "interface_format": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "model_name": "gpt-4o",
                    "temperature": 0.7,
                    "max_tokens": 16384,
                    "timeout": 600,
                },
                defaults={"per_chapter_words": 4500, "planned_chapters": 100, "planned_total_words": 300000},
                estimate={"duration": "4周", "chapters": 100, "cost_usd": 120},
                highlights=["细腻感伤", "细致刻画", "更高质量"],
            ),
            cls(
                template_id="fast_experiment_scifi",
                name="快速实验（科幻/其他）",
                category="科幻/其他",
                description="零成本优先，适合快速验证灵感与流程（需要本地模型）。",
                recommended_config={
                    "interface_format": "Ollama",
                    "base_url": "http://localhost:11434/v1",
                    "model_name": "qwen2.5:7b",
                    "temperature": 0.9,
                    "max_tokens": 8192,
                    "timeout": 600,
                },
                defaults={"per_chapter_words": 2500, "planned_chapters": 20, "planned_total_words": 50000},
                estimate={"duration": "1天", "chapters": 20, "cost_usd": 0},
                highlights=["零成本", "快速尝试", "适合小样本迭代"],
            ),
            cls(
                template_id="pro_publishing_hybrid",
                name="专业出版（全类型）",
                category="全类型",
                description="质量与成本的平衡方案，适合长周期创作与出版级整理。",
                recommended_config={
                    "interface_format": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "model_name": "gpt-4o",
                    "temperature": 0.75,
                    "max_tokens": 16384,
                    "timeout": 600,
                },
                defaults={"per_chapter_words": 3500, "planned_chapters": 200, "planned_total_words": 350000},
                estimate={"duration": "6周", "chapters": 200, "cost_usd": 80},
                highlights=["成本优化", "质量保证", "适合长期项目"],
            ),
        ]

    @staticmethod
    def _safe_folder_name(name: str) -> str:
        name = name.strip() or "NovelProject"
        name = re.sub(r"[\\/:*?\"<>|]", "_", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name[:64]

    @classmethod
    def create_project_directory(cls, parent_dir: str, project_name: str) -> str:
        base = Path(parent_dir).expanduser().resolve()
        base.mkdir(parents=True, exist_ok=True)

        folder = cls._safe_folder_name(project_name)
        candidate = base / folder
        if not candidate.exists():
            candidate.mkdir(parents=True, exist_ok=True)
            return str(candidate)

        for i in range(2, 1000):
            candidate = base / f"{folder}_{i}"
            if not candidate.exists():
                candidate.mkdir(parents=True, exist_ok=True)
                return str(candidate)

        raise RuntimeError("无法创建唯一的项目目录")

    @staticmethod
    def init_project_files(project_dir: str, project_meta: dict[str, Any]) -> None:
        p = Path(project_dir)
        (p / "chapters").mkdir(parents=True, exist_ok=True)

        def write_text(rel_path: str, content: str):
            target = p / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        write_text("project.json", json.dumps(project_meta, ensure_ascii=False, indent=2))
        write_text("Novel_architecture.txt", "")
        write_text("Novel_directory.txt", "")
        write_text("global_summary.txt", "")
        write_text("character_state.txt", "")

    @staticmethod
    def load_example_projects_index() -> list[dict[str, Any]]:
        if EXAMPLE_PROJECTS_INDEX_PATH.exists():
            try:
                return json.loads(EXAMPLE_PROJECTS_INDEX_PATH.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    @staticmethod
    def clone_example_project(example_id: str, dest_parent_dir: str, new_project_name: Optional[str] = None) -> str:
        src = (EXAMPLE_PROJECTS_DIR / example_id).resolve()
        if not src.exists():
            raise FileNotFoundError(f"示例项目不存在: {example_id}")

        index = {x.get("example_id"): x for x in ProjectTemplate.load_example_projects_index()}
        title = index.get(example_id, {}).get("title", example_id)
        name = new_project_name or title

        dest = ProjectTemplate.create_project_directory(dest_parent_dir, name)
        shutil.rmtree(dest, ignore_errors=True)
        shutil.copytree(src, dest)
        return dest


class OnboardingWizard(ctk.CTkToplevel):
    """交互式新手引导向导。

    目标：让新用户在 5 分钟内创建第一个小说项目。
    """

    def __init__(self, gui, *, on_close=None):
        super().__init__(gui.master)
        self.gui = gui
        self.on_close = on_close

        self.title("新手引导")
        self.geometry("860x620")
        self.minsize(820, 580)
        self.transient(gui.master)
        self.grab_set()

        self.templates = ProjectTemplate.load_all()
        self.template_by_id = {t.template_id: t for t in self.templates}

        self.selected_genre_type = ctk.StringVar(value="玄幻/仙侠")
        self.selected_template_id = ctk.StringVar(value=self.templates[0].template_id if self.templates else "")

        self.novel_name_var = ctk.StringVar(value="")
        self.author_name_var = ctk.StringVar(value="")
        self.synopsis_var = ctk.StringVar(value="")

        self.project_parent_dir_var = ctk.StringVar(value=str(Path.home()))

        self.planned_total_words_var = ctk.IntVar(value=120000)
        self.per_chapter_words_var = ctk.IntVar(value=3000)
        self.planned_chapters_var = ctk.IntVar(value=40)

        self.llm_setup_choice_var = ctk.StringVar(value="recommended")  # recommended/manual/later

        self._created_project_dir: str | None = None

        self._build_ui()
        self._show_step(0)

        self.protocol("WM_DELETE_WINDOW", self._handle_close)

    # ==================== UI 构建 ====================

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        header.grid_columnconfigure(0, weight=1)

        self.step_title = ctk.CTkLabel(header, text="", font=("Microsoft YaHei", 18, "bold"))
        self.step_title.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))

        self.step_subtitle = ctk.CTkLabel(header, text="", font=("Microsoft YaHei", 12))
        self.step_subtitle.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))

        self.progress_label = ctk.CTkLabel(header, text="", font=("Microsoft YaHei", 11))
        self.progress_label.grid(row=0, column=1, sticky="e", padx=12, pady=(10, 0))

        self.container = ctk.CTkFrame(self)
        self.container.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.footer = ctk.CTkFrame(self)
        self.footer.grid(row=2, column=0, sticky="ew", padx=12, pady=(6, 12))
        self.footer.grid_columnconfigure(0, weight=1)

        self.btn_back = ctk.CTkButton(self.footer, text="上一步", width=110, command=self._prev_step)
        self.btn_back.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.btn_help = ctk.CTkButton(self.footer, text="帮助", width=110, command=self._show_help)
        self.btn_help.grid(row=0, column=0, sticky="w", padx=(130, 0), pady=10)

        self.btn_skip = ctk.CTkButton(self.footer, text="跳过", width=110, fg_color="#444", command=self._skip)
        self.btn_skip.grid(row=0, column=0, sticky="w", padx=(250, 0), pady=10)

        self.btn_next = ctk.CTkButton(self.footer, text="下一步", width=140, command=self._next_step)
        self.btn_next.grid(row=0, column=1, sticky="e", padx=10, pady=10)

        self.steps: list[ctk.CTkFrame] = []
        self.steps.append(self._build_step_welcome())
        self.steps.append(self._build_step_genre())
        self.steps.append(self._build_step_basic_info())
        self.steps.append(self._build_step_llm())
        self.steps.append(self._build_step_finish())

    def _build_step_welcome(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.container)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(frame)
        inner.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        inner.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(inner, text="欢迎使用 AI 小说生成器", font=("Microsoft YaHei", 24, "bold"))
        title.grid(row=0, column=0, sticky="w", pady=(0, 15))

        desc = ctk.CTkLabel(
            inner,
            text=(
                "只需 5 分钟，创建你的第一部小说项目。\n\n"
                "这个向导会帮你：\n"
                "1) 选择题材与模板\n"
                "2) 填写基本信息并创建项目文件夹\n"
                "3) 应用推荐模型配置（可跳过/可稍后设置）"
            ),
            font=("Microsoft YaHei", 13),
            justify="left",
        )
        desc.grid(row=1, column=0, sticky="w")

        tips = ctk.CTkLabel(
            inner,
            text="随时可在菜单：帮助 → 新手教程 重新打开。",
            font=("Microsoft YaHei", 12),
            text_color="#9aa0a6",
        )
        tips.grid(row=2, column=0, sticky="w", pady=(15, 0))

        return frame

    def _build_step_genre(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.container)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(frame)
        left.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="选择小说类型", font=("Microsoft YaHei", 16, "bold")).grid(
            row=0, column=0, sticky="w", padx=15, pady=(15, 8)
        )

        types = [
            ("玄幻/仙侠", "示例：热血修仙、门派升级、秘境探险"),
            ("言情/现代", "示例：重逢、成长、治愈系日常"),
            ("科幻/未来", "示例：星际航行、AI、末日生存"),
            ("悬疑/恐怖", "示例：密室、连环谜题、心理惊悚"),
            ("其他", "示例：历史、奇幻、轻小说、实验写作"),
        ]

        for i, (k, hint) in enumerate(types, start=1):
            btn = ctk.CTkRadioButton(
                left,
                text=f"{k}  ·  {hint}",
                variable=self.selected_genre_type,
                value=k,
                command=self._on_genre_changed,
            )
            btn.grid(row=i, column=0, sticky="w", padx=15, pady=8)

        right = ctk.CTkFrame(frame)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="推荐项目模板", font=("Microsoft YaHei", 16, "bold")).grid(
            row=0, column=0, sticky="w", padx=15, pady=(15, 8)
        )

        self.template_menu = ctk.CTkOptionMenu(
            right,
            values=[t.name for t in self.templates],
            command=self._on_template_selected_by_name,
            font=("Microsoft YaHei", 12),
        )
        self.template_menu.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))

        self.template_summary = ctk.CTkTextbox(right, wrap="word", height=260, font=("Microsoft YaHei", 12))
        self.template_summary.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 10))
        self.template_summary.configure(state="disabled")

        hint = ctk.CTkLabel(
            right,
            text="模板只是一组推荐参数，你之后随时可以更改。",
            font=("Microsoft YaHei", 11),
            text_color="#9aa0a6",
        )
        hint.grid(row=3, column=0, sticky="w", padx=15)

        self._sync_template_ui_from_state()
        return frame

    def _build_step_basic_info(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.container)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(1, weight=1)

        row = 0
        title = ctk.CTkLabel(frame, text="填写基本信息", font=("Microsoft YaHei", 16, "bold"))
        title.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 10))
        row += 1

        def label_with_help(text: str, tooltip_key: str, r: int):
            left_frame = ctk.CTkFrame(frame, fg_color="transparent")
            left_frame.grid(row=r, column=0, sticky="e", padx=(20, 8), pady=8)

            label = ctk.CTkLabel(left_frame, text=text, font=("Microsoft YaHei", 12))
            label.pack(side="left")

            btn = ctk.CTkButton(
                left_frame,
                text="?",
                width=22,
                height=22,
                font=("Microsoft YaHei", 10),
                command=lambda: messagebox.showinfo("参数说明", tooltips.get(tooltip_key, "暂无说明")),
            )
            btn.pack(side="left", padx=(6, 0))
            attach_hover_tooltip(btn, tooltips.get(tooltip_key, ""))

        label_with_help("小说名称:", "novel_name", row)
        ctk.CTkEntry(frame, textvariable=self.novel_name_var, font=("Microsoft YaHei", 12)).grid(
            row=row, column=1, sticky="ew", padx=(0, 20), pady=8
        )
        row += 1

        label_with_help("作者名:", "author_name", row)
        ctk.CTkEntry(frame, textvariable=self.author_name_var, font=("Microsoft YaHei", 12)).grid(
            row=row, column=1, sticky="ew", padx=(0, 20), pady=8
        )
        row += 1

        label_with_help("简介:", "synopsis", row)
        self.synopsis_text = ctk.CTkTextbox(frame, height=120, wrap="word", font=("Microsoft YaHei", 12))
        self.synopsis_text.grid(row=row, column=1, sticky="nsew", padx=(0, 20), pady=8)
        frame.grid_rowconfigure(row, weight=1)
        row += 1

        label_with_help("计划总字数:", "planned_total_words", row)
        slider_frame = ctk.CTkFrame(frame)
        slider_frame.grid(row=row, column=1, sticky="ew", padx=(0, 20), pady=8)
        slider_frame.grid_columnconfigure(0, weight=1)

        self.words_value_label = ctk.CTkLabel(slider_frame, text="", font=("Microsoft YaHei", 12))
        self.words_value_label.grid(row=0, column=1, padx=(10, 0))

        self.words_slider = ctk.CTkSlider(
            slider_frame,
            from_=50000,
            to=500000,
            number_of_steps=450,
            variable=self.planned_total_words_var,
            command=lambda _v: self._update_planned_chapters(),
        )
        self.words_slider.grid(row=0, column=0, sticky="ew")
        row += 1

        label_with_help("计划章数:", "planned_chapters", row)
        self.chapters_label = ctk.CTkLabel(frame, text="", font=("Microsoft YaHei", 12))
        self.chapters_label.grid(row=row, column=1, sticky="w", padx=(0, 20), pady=8)
        row += 1

        label_with_help("项目保存位置:", "project_location", row)
        parent_frame = ctk.CTkFrame(frame)
        parent_frame.grid(row=row, column=1, sticky="ew", padx=(0, 20), pady=8)
        parent_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(parent_frame, textvariable=self.project_parent_dir_var, font=("Microsoft YaHei", 12)).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ctk.CTkButton(parent_frame, text="浏览...", width=80, command=self._choose_parent_dir).grid(
            row=0, column=1, sticky="e"
        )

        self._apply_template_defaults_to_basic_info()
        self._update_planned_chapters()
        return frame

    def _build_step_llm(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.container)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="配置 LLM", font=("Microsoft YaHei", 16, "bold")).pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        self.llm_recommendation_label = ctk.CTkLabel(frame, text="", font=("Microsoft YaHei", 12), justify="left")
        self.llm_recommendation_label.pack(anchor="w", padx=20, pady=(0, 10))

        rb_frame = ctk.CTkFrame(frame)
        rb_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkRadioButton(
            rb_frame,
            text="选项A：使用推荐配置（自动应用模板推荐模型参数）",
            variable=self.llm_setup_choice_var,
            value="recommended",
        ).pack(anchor="w", padx=15, pady=8)

        ctk.CTkRadioButton(
            rb_frame,
            text="选项B：手动配置（打开详细配置界面）",
            variable=self.llm_setup_choice_var,
            value="manual",
        ).pack(anchor="w", padx=15, pady=8)

        ctk.CTkRadioButton(
            rb_frame,
            text="选项C：稍后配置（先用默认配置）",
            variable=self.llm_setup_choice_var,
            value="later",
        ).pack(anchor="w", padx=15, pady=8)

        info = ctk.CTkTextbox(frame, wrap="word", height=230, font=("Microsoft YaHei", 12))
        info.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        info.configure(state="normal")
        info.delete("0.0", "end")
        info.insert(
            "0.0",
            "提示：\n"
            "- 推荐配置会写入到你当前选中的 LLM 配置（更容易上手）。\n"
            "- 你可以在主界面右侧的【LLM Model settings】里随时修改。\n"
            "- 温度(Temperature)越高越有创意，越低越稳定（右侧 ? 可查看说明）。\n",
        )
        info.configure(state="disabled")

        self._refresh_llm_recommendation_text()
        return frame

    def _build_step_finish(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.container)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        self.finish_title = ctk.CTkLabel(frame, text="项目已创建", font=("Microsoft YaHei", 18, "bold"))
        self.finish_title.pack(anchor="w", padx=20, pady=(20, 10))

        self.finish_desc = ctk.CTkLabel(frame, text="", font=("Microsoft YaHei", 12), justify="left")
        self.finish_desc.pack(anchor="w", padx=20)

        links = ctk.CTkFrame(frame)
        links.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(links, text="下一步是什么？", font=("Microsoft YaHei", 14, "bold")).pack(
            anchor="w", padx=15, pady=(15, 8)
        )

        btns = ctk.CTkFrame(links)
        btns.pack(fill="x", padx=15, pady=(0, 15))
        btns.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(btns, text="生成小说设定", command=self._quick_generate_architecture).grid(
            row=0, column=0, padx=8, pady=8, sticky="ew"
        )
        ctk.CTkButton(btns, text="查看示例项目", command=self._open_example_dialog).grid(
            row=0, column=1, padx=8, pady=8, sticky="ew"
        )
        ctk.CTkButton(btns, text="阅读文档", command=self._open_docs).grid(
            row=0, column=2, padx=8, pady=8, sticky="ew"
        )

        footer = ctk.CTkFrame(frame)
        footer.pack(fill="x", padx=20, pady=(0, 20))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(footer, text="现在开始", command=self._start_now).grid(
            row=0, column=0, sticky="e", padx=8, pady=8
        )
        ctk.CTkButton(footer, text="稍后", fg_color="#444", command=self._handle_close).grid(
            row=0, column=1, sticky="e", padx=8, pady=8
        )

        return frame

    # ==================== 步骤控制 ====================

    def _show_step(self, index: int):
        self.current_step = max(0, min(index, len(self.steps) - 1))
        for i, f in enumerate(self.steps):
            if i == self.current_step:
                f.tkraise()
            else:
                pass

        titles = [
            ("欢迎", "只需 5 分钟，创建你的第一部小说"),
            ("第2步：选择小说类型", "选择题材，并挑选一个合适的项目模板"),
            ("第3步：填写基本信息", "填写项目名称/简介/计划字数，并选择保存位置"),
            ("第4步：配置 LLM", "使用推荐配置，或稍后再设置"),
            ("第5步：开始创作", "项目已创建，可以立即开始生成"),
        ]
        title, subtitle = titles[self.current_step]
        self.step_title.configure(text=title)
        self.step_subtitle.configure(text=subtitle)
        self.progress_label.configure(text=f"{self.current_step + 1}/{len(self.steps)}")

        if self.current_step == 3:
            # 模板选择可能在前一步变化，这里确保推荐文案保持最新
            try:
                self._refresh_llm_recommendation_text()
            except Exception:
                pass

        self.btn_back.configure(state="normal" if self.current_step > 0 else "disabled")

        if self.current_step == 0:
            self.btn_next.configure(text="开始")
        elif self.current_step == len(self.steps) - 1:
            self.btn_next.configure(text="完成", state="disabled")
        else:
            self.btn_next.configure(text="下一步", state="normal")

    def _next_step(self):
        if self.current_step == 0:
            self._show_step(1)
            return

        if self.current_step == 1:
            self._sync_template_ui_from_state()
            self._show_step(2)
            return

        if self.current_step == 2:
            if not self._validate_basic_info():
                return
            self._show_step(3)
            return

        if self.current_step == 3:
            try:
                self._create_project_and_apply_to_gui()
            except Exception as e:
                messagebox.showerror("错误", f"创建项目失败: {e}")
                return
            self._show_step(4)
            return

    def _prev_step(self):
        self._show_step(self.current_step - 1)

    # ==================== Step 2: 类型/模板 ====================

    def _on_genre_changed(self):
        mapping = {
            "玄幻/仙侠": "standard_webnovel_xuanhuan",
            "言情/现代": "high_quality_romance_modern",
            "科幻/未来": "fast_experiment_scifi",
            "悬疑/恐怖": "pro_publishing_hybrid",
            "其他": "pro_publishing_hybrid",
        }
        tpl_id = mapping.get(self.selected_genre_type.get(), self.templates[0].template_id if self.templates else "")
        if tpl_id:
            self.selected_template_id.set(tpl_id)
        self._apply_template_defaults_to_basic_info()
        self._sync_template_ui_from_state()
        self._refresh_llm_recommendation_text()

    def _on_template_selected_by_name(self, template_name: str):
        for t in self.templates:
            if t.name == template_name:
                self.selected_template_id.set(t.template_id)
                break
        self._apply_template_defaults_to_basic_info()
        self._sync_template_ui_from_state()
        self._refresh_llm_recommendation_text()

    def _sync_template_ui_from_state(self):
        tpl = self._get_selected_template()
        if not tpl:
            return

        if hasattr(self, "template_menu"):
            self.template_menu.set(tpl.name)

        if hasattr(self, "template_summary"):
            text = (
                f"{tpl.name}\n"
                f"类别：{tpl.category}\n\n"
                f"{tpl.description}\n\n"
                f"推荐配置：\n"
                f"- 模型：{tpl.recommended_config.get('model_name')}\n"
                f"- 温度：{tpl.recommended_config.get('temperature')}\n"
                f"- 最大 tokens：{tpl.recommended_config.get('max_tokens')}\n\n"
                f"预计：{tpl.estimate.get('duration')} · {tpl.estimate.get('chapters')} 章 · 约 ${tpl.estimate.get('cost_usd')}\n\n"
                f"特点：{', '.join(tpl.highlights)}\n"
            )
            self.template_summary.configure(state="normal")
            self.template_summary.delete("0.0", "end")
            self.template_summary.insert("0.0", text)
            self.template_summary.configure(state="disabled")

    def _get_selected_template(self) -> Optional[ProjectTemplate]:
        tpl_id = self.selected_template_id.get()
        return self.template_by_id.get(tpl_id)

    # ==================== Step 3: 基本信息 ====================

    def _choose_parent_dir(self):
        selected = filedialog.askdirectory(initialdir=self.project_parent_dir_var.get())
        if selected:
            self.project_parent_dir_var.set(selected)

    def _apply_template_defaults_to_basic_info(self):
        tpl = self._get_selected_template()
        if not tpl:
            return
        try:
            self.per_chapter_words_var.set(int(tpl.defaults.get("per_chapter_words", 3000)))
            self.planned_total_words_var.set(int(tpl.defaults.get("planned_total_words", 120000)))
        except Exception:
            pass
        self._update_planned_chapters()

    def _update_planned_chapters(self):
        total_words = int(self.planned_total_words_var.get())
        per_chapter = max(500, int(self.per_chapter_words_var.get() or 3000))
        chapters = max(5, round(total_words / per_chapter))
        self.planned_chapters_var.set(chapters)

        if hasattr(self, "words_value_label"):
            self.words_value_label.configure(text=f"{total_words // 1000}k")
        if hasattr(self, "chapters_label"):
            self.chapters_label.configure(text=f"约 {chapters} 章（按每章约 {per_chapter} 字估算）")

    def _validate_basic_info(self) -> bool:
        name = self.novel_name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请填写小说名称")
            return False

        synopsis = self.synopsis_text.get("0.0", "end").strip()
        self.synopsis_var.set(synopsis)

        parent_dir = self.project_parent_dir_var.get().strip()
        if not parent_dir:
            messagebox.showwarning("提示", "请选择项目保存位置")
            return False

        return True

    # ==================== Step 4/5: 创建项目 + 应用配置 ====================

    def _create_project_and_apply_to_gui(self):
        tpl = self._get_selected_template()
        if not tpl:
            raise RuntimeError("未选择模板")

        project_dir = ProjectTemplate.create_project_directory(self.project_parent_dir_var.get(), self.novel_name_var.get())
        project_meta = {
            "title": self.novel_name_var.get().strip(),
            "author": self.author_name_var.get().strip(),
            "synopsis": self.synopsis_var.get().strip(),
            "genre_type": self.selected_genre_type.get().strip(),
            "template_id": tpl.template_id,
            "created_at": datetime.now().isoformat(),
        }
        ProjectTemplate.init_project_files(project_dir, project_meta)
        self._created_project_dir = project_dir

        self._apply_project_to_gui(project_dir)

        choice = self.llm_setup_choice_var.get()
        if choice == "recommended":
            self._apply_recommended_llm_config(tpl)
        elif choice == "manual":
            self._open_manual_config_hint()

        self._mark_onboarding_completed(skipped=False)

        self.finish_desc.configure(
            text=(
                f"项目路径：{project_dir}\n\n"
                "你可以：\n"
                "- 先点【生成小说设定】生成 Novel_architecture.txt\n"
                "- 再点【生成目录】生成 Novel_directory.txt\n"
                "- 最后用【生成草稿/定稿章节】逐章写作"
            )
        )

    def _apply_project_to_gui(self, project_dir: str):
        self.gui.filepath_var.set(project_dir)

        genre = self.selected_genre_type.get().strip()
        self.gui.genre_var.set(genre.split("/")[0] if "/" in genre else genre)

        self.gui.num_chapters_var.set(str(int(self.planned_chapters_var.get())))
        self.gui.word_number_var.set(str(int(self.per_chapter_words_var.get())))

        topic = self.synopsis_var.get().strip() or self.novel_name_var.get().strip()
        try:
            self.gui.topic_text.delete("0.0", "end")
            self.gui.topic_text.insert("0.0", topic)
        except Exception:
            pass

        try:
            self.gui.user_guide_text.delete("0.0", "end")
            self.gui.user_guide_text.insert("0.0", "写作风格：清晰、连贯、章节结尾留悬念。")
        except Exception:
            pass

        try:
            self.gui.safe_log(f"✅ 已创建项目并设置保存路径：{project_dir}")
        except Exception:
            pass

    def _apply_recommended_llm_config(self, tpl: ProjectTemplate):
        cfg_name = self.gui.interface_config_var.get()
        if not cfg_name:
            cfg_name = next(iter(self.gui.loaded_config.get("llm_configs", {}).keys()), "")
        if not cfg_name:
            raise RuntimeError("找不到可写入的 LLM 配置")

        llm_cfg = self.gui.loaded_config.setdefault("llm_configs", {}).setdefault(cfg_name, {})
        llm_cfg.update(
            {
                "interface_format": tpl.recommended_config.get("interface_format", llm_cfg.get("interface_format", "OpenAI")),
                "base_url": tpl.recommended_config.get("base_url", llm_cfg.get("base_url", "")),
                "model_name": tpl.recommended_config.get("model_name", llm_cfg.get("model_name", "")),
                "temperature": float(tpl.recommended_config.get("temperature", llm_cfg.get("temperature", 0.7))),
                "max_tokens": int(tpl.recommended_config.get("max_tokens", llm_cfg.get("max_tokens", 8192))),
                "timeout": int(tpl.recommended_config.get("timeout", llm_cfg.get("timeout", 600))),
            }
        )

        # 更新 UI 变量（右侧配置区会立刻反映）
        self.gui.interface_format_var.set(llm_cfg.get("interface_format", "OpenAI"))
        self.gui.base_url_var.set(llm_cfg.get("base_url", ""))
        self.gui.model_name_var.set(llm_cfg.get("model_name", ""))
        self.gui.temperature_var.set(float(llm_cfg.get("temperature", 0.7)))
        self.gui.max_tokens_var.set(int(llm_cfg.get("max_tokens", 8192)))
        self.gui.timeout_var.set(int(llm_cfg.get("timeout", 600)))

        # 统一各阶段使用同一配置，降低新手复杂度
        choose = self.gui.loaded_config.setdefault("choose_configs", {})
        choose.update(
            {
                "prompt_draft_llm": cfg_name,
                "chapter_outline_llm": cfg_name,
                "architecture_llm": cfg_name,
                "final_chapter_llm": cfg_name,
                "consistency_review_llm": cfg_name,
            }
        )
        self.gui.prompt_draft_llm_var.set(cfg_name)
        self.gui.chapter_outline_llm_var.set(cfg_name)
        self.gui.architecture_llm_var.set(cfg_name)
        self.gui.final_chapter_llm_var.set(cfg_name)
        self.gui.consistency_review_llm_var.set(cfg_name)

        save_config(self.gui.loaded_config, self.gui.config_file)

        try:
            self.gui.safe_log(f"✅ 已应用模板推荐模型配置到：{cfg_name}")
        except Exception:
            pass

    def _open_manual_config_hint(self):
        try:
            self.gui.tabview.set("Main Functions")
            self.gui.config_tabview.set("LLM Model settings")
        except Exception:
            pass

        messagebox.showinfo(
            "手动配置",
            "已为你切换到主界面右侧的 LLM 配置区。\n"
            "完成后可回到向导继续。\n\n"
            "提示：如果你不确定如何填写，建议先选择“使用推荐配置”。",
        )

    def _mark_onboarding_completed(self, *, skipped: bool):
        onboarding = self.gui.loaded_config.setdefault("onboarding", {})
        onboarding.update(
            {
                "completed": True,
                "skipped": bool(skipped),
                "completed_at": datetime.now().isoformat(),
            }
        )
        save_config(self.gui.loaded_config, self.gui.config_file)

    # ==================== Step 4: 推荐文本 ====================

    def _refresh_llm_recommendation_text(self):
        tpl = self._get_selected_template()
        if not tpl:
            self.llm_recommendation_label.configure(text="")
            return

        cfg = tpl.recommended_config
        self.llm_recommendation_label.configure(
            text=(
                "基于你选择的模板，推荐如下：\n"
                f"- 模型：{cfg.get('model_name')}\n"
                f"- 温度：{cfg.get('temperature')}（点右侧 ? 可查看说明）\n"
                f"- Max Tokens：{cfg.get('max_tokens')}\n"
                "\n如果你打算使用本地模型：请先安装并运行 Ollama，然后选择推荐配置。"
            )
        )

    # ==================== Step 5: 快捷操作 ====================

    def _quick_generate_architecture(self):
        self._start_now()
        try:
            self.gui.generate_novel_architecture_ui()
        except Exception:
            pass

    def _open_docs(self):
        try:
            readme = str((_project_root() / "README.md").resolve())
            webbrowser.open(f"file://{readme}")
        except Exception:
            messagebox.showinfo("文档", "未能打开文档，请查看项目根目录 README.md")

    def _open_example_dialog(self):
        examples = ProjectTemplate.load_example_projects_index()
        if not examples:
            messagebox.showinfo("示例项目", "未找到内置示例项目资源。")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("示例项目")
        dialog.geometry("640x420")
        dialog.transient(self)
        dialog.grab_set()

        dialog.grid_rowconfigure(1, weight=1)
        dialog.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dialog, text="选择一个示例项目进行克隆", font=("Microsoft YaHei", 14, "bold")).grid(
            row=0, column=0, sticky="w", padx=15, pady=(15, 8)
        )

        list_frame = ctk.CTkScrollableFrame(dialog)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        list_frame.grid_columnconfigure(0, weight=1)

        selected_id = ctk.StringVar(value=examples[0].get("example_id", ""))

        for idx, ex in enumerate(examples):
            ex_id = ex.get("example_id", "")
            title = ex.get("title", ex_id)
            tagline = ex.get("tagline", "")
            genre = ex.get("genre", "")
            chapters = ex.get("chapters_included", "")

            rb = ctk.CTkRadioButton(
                list_frame,
                text=f"{title}  ·  {genre}  ·  {tagline}（内含 {chapters} 章）",
                variable=selected_id,
                value=ex_id,
            )
            rb.grid(row=idx, column=0, sticky="w", padx=10, pady=8)

        bottom = ctk.CTkFrame(dialog)
        bottom.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        bottom.grid_columnconfigure((0, 1), weight=1)

        def clone_and_open():
            parent = filedialog.askdirectory(initialdir=self.project_parent_dir_var.get(), title="选择克隆到的目录")
            if not parent:
                return
            try:
                new_dir = ProjectTemplate.clone_example_project(selected_id.get(), parent)
            except Exception as e:
                messagebox.showerror("错误", f"克隆失败: {e}")
                return

            dialog.destroy()
            self._start_now()
            self.gui.filepath_var.set(new_dir)
            try:
                self.gui.safe_log(f"✅ 已克隆并打开示例项目：{new_dir}")
            except Exception:
                pass

        ctk.CTkButton(bottom, text="克隆并打开", command=clone_and_open).grid(row=0, column=0, sticky="e", padx=8, pady=8)
        ctk.CTkButton(bottom, text="关闭", fg_color="#444", command=dialog.destroy).grid(row=0, column=1, sticky="e", padx=8, pady=8)

    def _start_now(self):
        try:
            self.gui.tabview.set("Main Functions")
        except Exception:
            pass
        self._handle_close()

    # ==================== 全局操作 ====================

    def _show_help(self):
        messagebox.showinfo(
            "新手引导帮助",
            "建议流程：\n"
            "1) 先选一个模板（不用纠结，之后可随时改）\n"
            "2) 填好名称与简介，选择保存位置\n"
            "3) 选择“使用推荐配置”即可开始\n\n"
            "如果你对 Temperature/Max Tokens 等概念不熟悉，点界面上的 ? 会显示说明。",
        )

    def _skip(self):
        self._mark_onboarding_completed(skipped=True)
        self._handle_close()

    def _handle_close(self):
        try:
            self.grab_release()
        except Exception:
            pass

        try:
            self.destroy()
        except Exception:
            pass

        if callable(self.on_close):
            try:
                self.on_close()
            except Exception:
                pass

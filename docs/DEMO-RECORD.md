# How to Record Demo Assets | 如何录制演示素材

We need two types of assets: **Static Screenshots** (for README) and a **Live Demo GIF**.

我们需要两类素材：**静态截图**（用于 README）和**动态演示 GIF**。

---

## 1. Static Screenshots (Required) | 静态截图（必须）

**Target | 目标**:
- `docs/images/streamlit-dashboard.png`
- `docs/images/streamlit-workbench.png`
- `docs/images/streamlit-knowledge-base.png`

1.  **Start Streamlit | 启动 Streamlit**:
    ```bash
    streamlit run frontend/Home.py
    ```
2.  **Dashboard | 仪表盘**: Take a screenshot of the main **Dashboard** page.
    -   Save as: `docs/images/streamlit-dashboard.png`.
    -   截取 **Dashboard** 主页的屏幕截图，保存为 `docs/images/streamlit-dashboard.png`。
3.  **Workbench | 工作台**: Navigate to **Assessment Workbench**, upload a file, and wait for results.
    -   Take a screenshot of the results page (Risk/Compliance tabs).
    -   Save as: `docs/images/streamlit-workbench.png`.
    -   进入 **Assessment Workbench**，上传文件并等待结果。截取结果页（风险/合规标签页），保存为 `docs/images/streamlit-workbench.png`。
4.  **Knowledge Base | 知识库**: Navigate to **Knowledge Base**.
    -   Take a screenshot of the upload interface.
    -   Save as: `docs/images/streamlit-knowledge-base.png`.
    -   进入 **Knowledge Base**。截取上传界面，保存为 `docs/images/streamlit-knowledge-base.png`。

---

## 2. Live Demo GIF (Optional) | 动态演示 GIF（可选）

**Target | 目标**: `docs/images/demo-assessment.gif`.

1.  **Record | 录制**: (e.g. using QuickTime, LICEcap, or ScreenToGif).
    -   使用录屏工具（如 QuickTime, LICEcap, ScreenToGif）。
2.  **Workflow (30-60s) | 流程（30-60秒）**:
    -   Start on Dashboard.
    -   Click **Assessment Workbench**.
    -   Upload `examples/test_iso_27001_extract.pdf`.
    -   Click **Start Assessment**.
    -   Wait for the "Processing" steps.
    -   Show the final report tabs (Risk, Compliance).
    -   从 Dashboard 开始。点击 Assessment Workbench。上传示例文件。点击开始评估。等待处理。展示最终报告。
3.  **Save | 保存**: Export as GIF to `docs/images/demo-assessment.gif`.
    -   导出为 GIF，保存至 `docs/images/demo-assessment.gif`。

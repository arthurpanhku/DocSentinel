# How to Record Demo Assets | 如何录制演示素材

We need two types of assets: **Static Screenshots** (for README) and a **Live Demo GIF**.

---

## 1. Static Screenshots (Required) | 静态截图（必须）

**Target**: 
- `docs/images/streamlit-dashboard.png`
- `docs/images/streamlit-workbench.png`
- `docs/images/streamlit-knowledge-base.png`

1.  **Start Streamlit**:
    ```bash
    streamlit run frontend/Home.py
    ```
2.  **Dashboard**: Take a screenshot of the main **Dashboard** page.
    -   Save as: `docs/images/streamlit-dashboard.png`.
3.  **Workbench**: Navigate to **Assessment Workbench**, upload a file, and wait for results.
    -   Take a screenshot of the results page (Risk/Compliance tabs).
    -   Save as: `docs/images/streamlit-workbench.png`.
4.  **Knowledge Base**: Navigate to **Knowledge Base**.
    -   Take a screenshot of the upload interface.
    -   Save as: `docs/images/streamlit-knowledge-base.png`.

---

## 2. Live Demo GIF (Optional) | 动态演示 GIF（可选）

**Target**: `docs/images/demo-assessment.gif`.

1.  **Record**: (e.g. using QuickTime, LICEcap, or ScreenToGif).
2.  **Workflow** (30-60s):
    -   Start on Dashboard.
    -   Click **Assessment Workbench**.
    -   Upload `examples/test_iso_27001_extract.pdf`.
    -   Click **Start Assessment**.
    -   Wait for the "Processing" steps.
    -   Show the final report tabs (Risk, Compliance).
3.  **Save**: Export as GIF to `docs/images/demo-assessment.gif`.


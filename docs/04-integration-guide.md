# 04 — Integration Guide | 集成指南

|                 |                                            |
| :-------------- | :----------------------------------------- |
| **Status**      | [ ] Draft \| [ ] In Review \| [ ] Approved |
| **Version**     | 0.1                                        |
| **Related PRD** | Section 5.2.7 Integrations, 5.2.8 IAM      |

---

## 1. Azure AD (Entra ID) | Identity Provider

### 1.1 App Registration

| Step               | Action                                                                | Config                                                                             |
| :----------------- | :-------------------------------------------------------------------- | :--------------------------------------------------------------------------------- |
| 1. Register App    | Create new registration in [Azure Portal](https://portal.azure.com/). | Tenant ID: `AAD_TENANT_ID`                                                         |
| 2. Client ID       | Copy Application (client) ID.                                         | `AAD_CLIENT_ID`                                                                    |
| 3. Client Secret   | Generate a client secret (or use Certificate).                        | `AAD_CLIENT_SECRET`                                                                |
| 4. Redirect URI    | Set Web Redirect URI.                                                 | `https://<your-domain>/auth/callback`                                              |
| 5. API Permissions | Add scopes.                                                           | `OpenID`, `email`, `profile`                                                       |
| 6. Discovery URL   | OIDC Metadata.                                                        | `https://login.microsoftonline.com/<tenant>/v2.0/.well-known/openid-configuration` |

### 1.2 Configuration (Example)

Add to `.env`:

```bash
# AAD / OIDC
AAD_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AAD_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AAD_CLIENT_SECRET=********
AAD_REDIRECT_URI=https://your-agent.example.com/auth/callback
OIDC_ISSUER=https://login.microsoftonline.com/{tenant_id}/v2.0
```

### 1.3 Network Requirements

-   **Outbound**: Allow access to `login.microsoftonline.com`.
-   **Inbound**: User browser must reach the Redirect URI.

### 1.4 RBAC Mapping (Optional)

| AAD Group                 | Agent Role | Implementation                 |
| :------------------------ | :--------- | :----------------------------- |
| `Security-Agent-Analysts` | `analyst`  | Map via `groups` claim in JWT. |
| `Security-Admins`         | `admin`    |                                |

---

## 2. ServiceNow | Project Management Platform

### 2.1 Target APIs

Confirm these APIs/Tables with your ServiceNow admin:

| Purpose               | Table / API                        | Description                 |
| :-------------------- | :--------------------------------- | :-------------------------- |
| **Project Data**      | `pm_project` / Project API         | ID, Name, Type, Owner.      |
| **Compliance Scope**  | Custom field (e.g. `u_compliance`) | Used to select KB scope.    |
| **Ticket Write-back** | `incident` / `task`                | To post assessment results. |

### 2.2 Field Mapping

| Agent Field    | ServiceNow Field    | Note               |
| :------------- | :------------------ | :----------------- |
| `project_id`   | `sys_id`            | Unique identifier. |
| `project_name` | `short_description` |                    |
| `project_type` | `u_project_type`    |                    |
| `department`   | `department`        |                    |

### 2.3 Authentication

| Method         | Description                     |
| :------------- | :------------------------------ |
| **Basic Auth** | Username + Password (Dev/Test). |
| **OAuth 2.0**  | Recommended for Production.     |

Config example:

```bash
SERVICENOW_INSTANCE=https://your-instance.service-now.com
SERVICENOW_USERNAME=integration_user
SERVICENOW_PASSWORD=********
```

### 2.4 Write-back Workflow (Optional)

1.  Agent completes assessment (status: `completed`).
2.  Agent calls ServiceNow API (e.g. `PATCH /api/now/table/task/{sys_id}`).
3.  Payload:
    ```json
    {
      "work_notes": "Assessment Completed. Report: https://agent/reports/{task_id}"
    }
    ```

---

## 3. Other Identity Providers (Optional)

If supporting Okta or Google Workspace:

1.  Register OIDC App.
2.  Configure `OIDC_ISSUER` and Client ID/Secret.
3.  Map claims to roles.

---

## 4. Compliance Exchange | 合规数据交换

DocSentinel can export governance controls and project evidence in OSCAL-style
JSON for downstream GRC, audit, and compliance-as-code workflows.

### 4.1 Control Catalog Export

```bash
curl "http://localhost:8000/api/v1/oscal/catalog?framework_ids=nist-ssdf"
```

The response includes resolved policy-pack controls grouped by family, source
framework properties, and OpenCRE search links for cross-framework requirement
mapping.

### 4.2 Project Assessment Results Export

```bash
curl "http://localhost:8000/api/v1/projects/{project_id}/oscal/assessment-results"
```

The response includes reviewed controls, evidence observations, and findings
derived from DocSentinel control status. Use this export to attach release-gate
evidence to external audit workpapers or compliance automation pipelines.

---

## 5. Changelog | 修订记录

| Version | Date    | Changes                                     |
| :------ | :------ | :------------------------------------------ |
| **0.1** | Initial | Draft AAD and ServiceNow integration guide. |

import {
  BrainCircuit,
  Database,
  FolderKanban,
  Gauge,
  ListChecks,
  Network,
  Settings,
  type LucideIcon
} from "lucide-react";

export type NavigationItem = {
  to: string;
  label: string;
  shortLabel: string;
  description: string;
  keywords: string[];
  icon: LucideIcon;
};

export type NavigationGroup = {
  label: string;
  items: NavigationItem[];
};

export const navigationGroups: NavigationGroup[] = [
  {
    label: "Workspace",
    items: [
      {
        to: "/",
        label: "Overview",
        shortLabel: "Overview",
        description: "Security posture and work requiring attention",
        keywords: ["dashboard", "command center", "metrics", "activity"],
        icon: Gauge
      }
    ]
  },
  {
    label: "Review & govern",
    items: [
      {
        to: "/assessments",
        label: "Assessment queue",
        shortLabel: "Assessments",
        description: "Submit evidence, review findings, and approve outcomes",
        keywords: ["review", "findings", "reports", "documents", "remediation"],
        icon: ListChecks
      },
      {
        to: "/governance",
        label: "Governance",
        shortLabel: "Governance",
        description: "Projects, controls, evidence, and readiness",
        keywords: ["controls", "policy", "compliance", "pallas", "projects"],
        icon: FolderKanban
      }
    ]
  },
  {
    label: "Agent operations",
    items: [
      {
        to: "/kb",
        label: "Knowledge base",
        shortLabel: "Knowledge",
        description: "Approved sources and retrieval inspection",
        keywords: ["rag", "documents", "context", "sources", "reindex"],
        icon: Database
      },
      {
        to: "/skills",
        label: "Skill library",
        shortLabel: "Skills",
        description: "Assessment personas, prompts, and frameworks",
        keywords: ["prompts", "personas", "agents", "frameworks"],
        icon: BrainCircuit
      },
      {
        to: "/integrations",
        label: "Agent gateway",
        shortLabel: "Gateway",
        description: "MCP and A2A endpoints, access, and capabilities",
        keywords: ["mcp", "a2a", "protocols", "integrations", "tools"],
        icon: Network
      }
    ]
  },
  {
    label: "System",
    items: [
      {
        to: "/settings",
        label: "Runtime settings",
        shortLabel: "Settings",
        description: "Model provider, API health, and local runtime",
        keywords: ["llm", "provider", "model", "configuration", "health"],
        icon: Settings
      }
    ]
  }
];

export const navigationItems = navigationGroups.flatMap((group) =>
  group.items.map((item) => ({ ...item, group: group.label }))
);

export function navigationItemForPath(pathname: string) {
  return (
    navigationItems.find((item) =>
      item.to === "/" ? pathname === "/" : pathname.startsWith(item.to)
    ) ?? navigationItems[0]
  );
}

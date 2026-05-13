export function formatDateTime(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

export function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(date);
}

export function percent(value?: number | null) {
  if (typeof value !== "number") return "-";
  return `${Math.round(value * 100)}%`;
}

export function truncateMiddle(value: string, length = 12) {
  if (value.length <= length) return value;
  const keep = Math.max(4, Math.floor((length - 1) / 2));
  return `${value.slice(0, keep)}…${value.slice(-keep)}`;
}

export function candidateTypeLabel(type: string) {
  const labels: Record<string, string> = {
    fact: "事实",
    evidence: "证据",
    todo: "待办",
    timeline: "时间线"
  };
  return labels[type] ?? type;
}

export function statusLabel(status: string) {
  const labels: Record<string, string> = {
    open: "进行中",
    closed: "已关闭",
    pending: "待处理",
    confirmed: "已确认",
    rejected: "已拒绝",
    draft: "草稿",
    failed: "失败",
    completed: "完成"
  };
  return labels[status] ?? status;
}

export function strengthLabel(strength?: string | null) {
  const labels: Record<string, string> = {
    unknown: "待判断",
    low: "弱",
    medium: "中",
    high: "强"
  };
  return labels[strength ?? ""] ?? (strength || "-");
}

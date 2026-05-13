<template>
  <span class="status-pill" :data-tone="tone">{{ label }}</span>
</template>

<script setup lang="ts">
defineProps<{
  label: string;
  tone?: "neutral" | "success" | "warning" | "danger";
}>();
</script>

<style scoped>
.status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--color-line);
  border-radius: 999px;
  color: var(--color-strong);
  background: #ffffff;
  font-size: 13px;
  white-space: nowrap;
}

.status-pill[data-tone="success"] {
  border-color: rgba(18, 184, 134, 0.35);
  color: #087f5b;
  background: var(--color-mint-soft);
}

.status-pill[data-tone="warning"] {
  border-color: rgba(245, 165, 36, 0.42);
  color: #9a6700;
  background: var(--color-amber-soft);
}

.status-pill[data-tone="danger"] {
  border-color: rgba(255, 107, 87, 0.4);
  color: #bd3324;
  background: var(--color-coral-soft);
}
</style>

<template>
  <div class="statistics-dashboard">
    <div class="stats-placeholder">
      <BarChart3 />
      <p>数据统计功能</p>
      <small>开发中...</small>
    </div>
  </div>
</template>

<script setup lang="ts">
import { BarChart3 } from 'lucide-vue-next'
</script>

<style scoped lang="scss">
@import '@/styles/design-system.scss';

.statistics-dashboard {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stats-placeholder {
  text-align: center;
  color: $text-tertiary;

  svg {
    width: 64px;
    height: 64px;
    margin-bottom: $spacing-4;
  }

  p {
    font-size: $font-size-lg;
    font-weight: $font-weight-semibold;
    margin-bottom: $spacing-2;
  }

  small {
    font-size: $font-size-sm;
  }
}
</style>

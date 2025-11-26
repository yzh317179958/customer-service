<template>
  <div class="knowledge-base">
    <div class="knowledge-placeholder">
      <BookOpen />
      <p>知识库功能</p>
      <small>开发中...</small>
    </div>
  </div>
</template>

<script setup lang="ts">
import { BookOpen } from 'lucide-vue-next'
</script>

<style scoped lang="scss">
@import '@/styles/design-system.scss';

.knowledge-base {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.knowledge-placeholder {
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

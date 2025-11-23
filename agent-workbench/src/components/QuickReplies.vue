<script setup lang="ts">
import { ref, computed } from 'vue'

const emit = defineEmits<{
  (e: 'select', content: string): void
}>()

// 快捷短语配置
const quickReplies = ref([
  {
    id: 1,
    category: '问候',
    items: [
      { id: 101, title: '欢迎语', content: '您好，我是人工客服，很高兴为您服务。请问有什么可以帮助您的？' },
      { id: 102, title: '稍等', content: '好的，请您稍等，我正在为您查询相关信息。' },
      { id: 103, title: '感谢等待', content: '感谢您的耐心等待，已为您查询到以下信息：' }
    ]
  },
  {
    id: 2,
    category: '产品',
    items: [
      { id: 201, title: '产品咨询', content: '关于您咨询的产品，我来为您详细介绍一下：' },
      { id: 202, title: '价格说明', content: '目前这款产品的价格是：' },
      { id: 203, title: '库存确认', content: '我帮您查询了一下库存，目前该产品：' }
    ]
  },
  {
    id: 3,
    category: '售后',
    items: [
      { id: 301, title: '退换货', content: '关于退换货，我们的政策是：7天无理由退换，15天质量问题可换货。请问您遇到了什么问题？' },
      { id: 302, title: '维修服务', content: '我们提供全国联保服务，您可以：1. 寄回总部维修；2. 到当地授权服务点维修。' },
      { id: 303, title: '物流查询', content: '我帮您查询了订单物流状态：' }
    ]
  },
  {
    id: 4,
    category: '结束',
    items: [
      { id: 401, title: '问题解决', content: '很高兴能帮助到您！如果还有其他问题，随时联系我们。祝您生活愉快！' },
      { id: 402, title: '后续跟进', content: '好的，我已记录您的问题，稍后会有专人跟进处理。请保持电话畅通。' },
      { id: 403, title: '评价邀请', content: '感谢您的咨询！如果您对本次服务满意，欢迎给我们一个好评。再见！' }
    ]
  }
])

// 搜索关键词
const searchKeyword = ref('')

// 当前展开的分类
const expandedCategory = ref<number | null>(null)

// 过滤后的快捷短语
const filteredReplies = computed(() => {
  if (!searchKeyword.value.trim()) {
    return quickReplies.value
  }

  const keyword = searchKeyword.value.toLowerCase()
  return quickReplies.value.map(category => ({
    ...category,
    items: category.items.filter(
      item =>
        item.title.toLowerCase().includes(keyword) ||
        item.content.toLowerCase().includes(keyword)
    )
  })).filter(category => category.items.length > 0)
})

// 切换分类展开
const toggleCategory = (categoryId: number) => {
  if (expandedCategory.value === categoryId) {
    expandedCategory.value = null
  } else {
    expandedCategory.value = categoryId
  }
}

// 选择快捷短语
const handleSelect = (content: string) => {
  emit('select', content)
}
</script>

<template>
  <div class="quick-replies">
    <div class="quick-replies-header">
      <h3>快捷短语</h3>
      <input
        v-model="searchKeyword"
        type="text"
        class="search-input"
        placeholder="搜索短语..."
      >
    </div>

    <div class="categories">
      <div
        v-for="category in filteredReplies"
        :key="category.id"
        class="category"
      >
        <div
          class="category-header"
          @click="toggleCategory(category.id)"
        >
          <span class="category-name">{{ category.category }}</span>
          <span class="category-count">{{ category.items.length }}</span>
          <span class="expand-icon" :class="{ expanded: expandedCategory === category.id }">
            ▶
          </span>
        </div>

        <transition name="slide">
          <div
            v-if="expandedCategory === category.id"
            class="category-items"
          >
            <div
              v-for="item in category.items"
              :key="item.id"
              class="reply-item"
              @click="handleSelect(item.content)"
            >
              <span class="reply-title">{{ item.title }}</span>
              <span class="reply-preview">{{ item.content.substring(0, 30) }}...</span>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <div v-if="filteredReplies.length === 0" class="no-results">
      未找到匹配的短语
    </div>
  </div>
</template>

<style scoped>
.quick-replies {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.quick-replies-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.quick-replies-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px 0;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
}

.search-input:focus {
  border-color: #667eea;
}

.categories {
  max-height: 300px;
  overflow-y: auto;
}

.category {
  border-bottom: 1px solid #f3f4f6;
}

.category:last-child {
  border-bottom: none;
}

.category-header {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.category-header:hover {
  background: #f9fafb;
}

.category-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.category-count {
  font-size: 12px;
  color: #9ca3af;
  margin-right: 8px;
}

.expand-icon {
  font-size: 10px;
  color: #9ca3af;
  transition: transform 0.2s;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.category-items {
  padding: 4px 8px 8px;
  background: #f9fafb;
}

.reply-item {
  padding: 8px 12px;
  margin-bottom: 4px;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.reply-item:hover {
  border-color: #667eea;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.1);
}

.reply-item:last-child {
  margin-bottom: 0;
}

.reply-title {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 2px;
}

.reply-preview {
  display: block;
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-results {
  padding: 20px;
  text-align: center;
  font-size: 13px;
  color: #9ca3af;
}

/* 动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  max-height: 300px;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>

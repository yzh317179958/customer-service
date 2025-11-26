<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  getQuickReplies,
  useQuickReply,
  replaceVariables,
  type QuickReply,
  type CategoryMetadata,
  type QuickReplyCategory
} from '../api/quickReplies'

const props = defineProps<{
  sessionName?: string      // 当前会话名称（用于获取客户信息）
  customerName?: string     // 客户姓名
  agentName?: string        // 坐席姓名
}>()

const emit = defineEmits<{
  (e: 'select', content: string): void
}>()

// 状态
const loading = ref(false)
const quickReplies = ref<QuickReply[]>([])
const categories = ref<CategoryMetadata[]>([])
const supportedVariables = ref<Record<string, string>>({})

// 搜索关键词
const searchKeyword = ref('')

// 当前展开的分类
const expandedCategory = ref<string | null>(null)

// 分类筛选
const selectedCategory = ref<QuickReplyCategory | null>(null)

// 错误状态
const error = ref<string | null>(null)

/**
 * 加载快捷回复数据
 */
const loadQuickReplies = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await getQuickReplies(selectedCategory.value || undefined)

    quickReplies.value = response.data.items
    categories.value = response.data.categories
    supportedVariables.value = response.data.variables

    console.log('✅ 快捷回复加载成功:', quickReplies.value.length, '条')
  } catch (err: any) {
    console.error('❌ 加载快捷回复失败:', err)
    error.value = err.response?.data?.detail || '加载快捷回复失败'
  } finally {
    loading.value = false
  }
}

/**
 * 按分类分组快捷回复
 */
const groupedReplies = computed(() => {
  const groups: Record<string, QuickReply[]> = {}

  quickReplies.value.forEach(reply => {
    if (!groups[reply.category]) {
      groups[reply.category] = []
    }
    groups[reply.category].push(reply)
  })

  return groups
})

/**
 * 过滤后的分类（根据搜索关键词）
 */
const filteredCategories = computed(() => {
  if (!searchKeyword.value.trim()) {
    return categories.value.map(cat => ({
      ...cat,
      items: groupedReplies.value[cat.key] || []
    })).filter(cat => cat.items.length > 0)
  }

  const keyword = searchKeyword.value.toLowerCase()

  return categories.value.map(cat => {
    const items = (groupedReplies.value[cat.key] || []).filter(
      item =>
        item.title.toLowerCase().includes(keyword) ||
        item.content.toLowerCase().includes(keyword)
    )
    return { ...cat, items }
  }).filter(cat => cat.items.length > 0)
})

/**
 * 切换分类展开
 */
const toggleCategory = (categoryKey: string) => {
  if (expandedCategory.value === categoryKey) {
    expandedCategory.value = null
  } else {
    expandedCategory.value = categoryKey
  }
}

/**
 * 获取变量替换的上下文
 */
const getVariableContext = (): Record<string, string> => {
  return {
    customer_name: props.customerName || '客户',
    agent_name: props.agentName || '客服',
    session_name: props.sessionName || '',
    // 可以添加更多上下文变量
  }
}

/**
 * 预览快捷回复内容（替换变量）
 */
const previewContent = (reply: QuickReply): string => {
  if (reply.variables.length === 0) {
    return reply.content
  }

  const context = getVariableContext()
  return replaceVariables(reply.content, context)
}

/**
 * 选择快捷短语
 */
const handleSelect = async (reply: QuickReply) => {
  try {
    // 获取替换变量后的内容
    const content = previewContent(reply)

    // 追踪使用次数
    await useQuickReply(reply.id)
    console.log(`✅ 使用快捷回复: ${reply.title} (ID: ${reply.id})`)

    // 发送到父组件
    emit('select', content)

    // 更新本地使用次数（可选，避免重新加载）
    const index = quickReplies.value.findIndex(r => r.id === reply.id)
    if (index !== -1) {
      quickReplies.value[index].usage_count++
    }
  } catch (err) {
    console.error('❌ 使用快捷回复失败:', err)
  }
}

/**
 * 格式化快捷键显示
 */
const formatShortcut = (shortcut?: string): string => {
  if (!shortcut) return ''
  // 将 "Ctrl+1" 转换为平台特定格式
  return shortcut.replace('Ctrl', navigator.platform.includes('Mac') ? '⌘' : 'Ctrl')
}

/**
 * 初始化加载
 */
onMounted(() => {
  loadQuickReplies()
})

/**
 * 监听分类筛选变化
 */
watch(selectedCategory, () => {
  loadQuickReplies()
})
</script>

<template>
  <div class="quick-replies">
    <div class="quick-replies-header">
      <h3>快捷短语</h3>

      <!-- 搜索框 -->
      <input
        v-model="searchKeyword"
        type="text"
        class="search-input"
        placeholder="搜索短语..."
      >

      <!-- 分类筛选 -->
      <div v-if="categories.length > 0" class="category-filter">
        <button
          class="filter-btn"
          :class="{ active: selectedCategory === null }"
          @click="selectedCategory = null"
        >
          全部
        </button>
        <button
          v-for="cat in categories"
          :key="cat.key"
          class="filter-btn"
          :class="{ active: selectedCategory === cat.key }"
          :style="{ borderColor: selectedCategory === cat.key ? cat.color : '' }"
          @click="selectedCategory = cat.key as QuickReplyCategory"
        >
          {{ cat.label }}
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error">
      <span>❌ {{ error }}</span>
      <button class="retry-btn" @click="loadQuickReplies">重试</button>
    </div>

    <!-- 快捷回复列表 -->
    <div v-else class="categories">
      <div
        v-for="category in filteredCategories"
        :key="category.key"
        class="category"
      >
        <div
          class="category-header"
          @click="toggleCategory(category.key)"
        >
          <span class="category-icon" :style="{ color: category.color }">
            {{ category.icon === 'MessageCircle' ? '💬' :
               category.icon === 'Package' ? '📦' :
               category.icon === 'Truck' ? '🚚' :
               category.icon === 'Wrench' ? '🔧' :
               category.icon === 'FileText' ? '📄' : '📌' }}
          </span>
          <span class="category-name">{{ category.label }}</span>
          <span class="category-count">{{ category.items.length }}</span>
          <span class="expand-icon" :class="{ expanded: expandedCategory === category.key }">
            ▶
          </span>
        </div>

        <transition name="slide">
          <div
            v-if="expandedCategory === category.key"
            class="category-items"
          >
            <div
              v-for="item in category.items"
              :key="item.id"
              class="reply-item"
              @click="handleSelect(item)"
            >
              <div class="reply-header">
                <span class="reply-title">{{ item.title }}</span>
                <span v-if="item.shortcut" class="reply-shortcut">
                  {{ formatShortcut(item.shortcut) }}
                </span>
              </div>
              <span class="reply-preview">
                {{ previewContent(item).substring(0, 50) }}{{ previewContent(item).length > 50 ? '...' : '' }}
              </span>
              <div class="reply-meta">
                <span class="usage-count">🔥 {{ item.usage_count }}次</span>
                <span v-if="item.variables.length > 0" class="has-variables">
                  🏷️ 含变量
                </span>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && !error && filteredCategories.length === 0" class="no-results">
      <span v-if="searchKeyword">未找到匹配的短语</span>
      <span v-else>暂无快捷回复</span>
    </div>
  </div>
</template>

<style scoped>
.quick-replies {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 500px;
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
  margin-bottom: 8px;
}

.search-input:focus {
  border-color: #667eea;
}

.category-filter {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 4px 10px;
  font-size: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  background: white;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.filter-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.loading,
.error {
  padding: 20px;
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.retry-btn {
  padding: 6px 12px;
  font-size: 12px;
  border: 1px solid #667eea;
  border-radius: 4px;
  background: white;
  color: #667eea;
  cursor: pointer;
  align-self: center;
}

.retry-btn:hover {
  background: #667eea;
  color: white;
}

.categories {
  flex: 1;
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

.category-icon {
  font-size: 16px;
  margin-right: 8px;
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
  padding: 10px 12px;
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

.reply-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.reply-title {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}

.reply-shortcut {
  font-size: 11px;
  color: #9ca3af;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 3px;
}

.reply-preview {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
  line-height: 1.4;
}

.reply-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
}

.usage-count {
  color: #f59e0b;
}

.has-variables {
  color: #8b5cf6;
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
  max-height: 500px;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>

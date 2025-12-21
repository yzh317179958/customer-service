<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

// 产品分类
const categories = [
  { id: 'all', name: 'All E-Bikes' },
  { id: 'city', name: 'City & Commuter' },
  { id: 'cargo', name: 'Cargo & Utility' },
  { id: 'fat', name: 'Fat Tire' },
  { id: 'carbon', name: 'Carbon Fiber' }
]

const activeCategory = ref('all')

interface Product {
  id: string
  name: string
  subtitle: string
  price: string
  originalPrice?: string
  image: string
  badge?: string
  badgeType?: 'hot' | 'new' | 'award' | 'sale'
  category: string[]
  features: string[]
  productShortName: string
}

const products = ref<Product[]>([
  {
    id: 'titan',
    name: 'Fiido Titan',
    subtitle: 'Fat Tire Cargo E-Bike',
    price: '$1,599',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-titan_1024x.webp',
    badge: 'Hot',
    badgeType: 'hot',
    category: ['all', 'cargo', 'fat'],
    features: ['750W Motor', '48V 15Ah Battery', '50+ Miles Range'],
    productShortName: 'Titan'
  },
  {
    id: 'm1-pro',
    name: 'Fiido M1 Pro',
    subtitle: 'Fat Tire Adventure E-Bike',
    price: '$1,299',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/7-m1-pro_a8e3269b-7ec7-4f38-a211-1cb2649c18ee_1024x.webp',
    badge: 'Best Seller',
    badgeType: 'hot',
    category: ['all', 'fat'],
    features: ['500W Motor', '48V 12.8Ah Battery', '60+ Miles Range'],
    productShortName: 'M1 Pro'
  },
  {
    id: 'c11-pro',
    name: 'Fiido C11 Pro',
    subtitle: 'City Commuter E-Bike',
    price: '$899',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-c11-pro_dce92f31-e919-4a94-b8b0-f9cb9b037d75_1024x.webp',
    badge: 'New',
    badgeType: 'new',
    category: ['all', 'city'],
    features: ['350W Motor', '36V 11.6Ah Battery', '40+ Miles Range'],
    productShortName: 'C11 Pro'
  },
  {
    id: 'air',
    name: 'Fiido Air',
    subtitle: 'Carbon Fiber Ultra-Light',
    price: '$2,499',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/c31-img-1_1024x.webp',
    badge: 'Red Dot Award',
    badgeType: 'award',
    category: ['all', 'carbon', 'city'],
    features: ['13.75kg Weight', 'Carbon Frame', 'Belt Drive'],
    productShortName: 'Air'
  },
  {
    id: 'c21',
    name: 'Fiido C21',
    subtitle: 'Step-Through City E-Bike',
    price: '$1,099',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-L.webp',
    category: ['all', 'city'],
    features: ['350W Motor', '36V 14.5Ah Battery', '55+ Miles Range'],
    productShortName: 'C21'
  },
  {
    id: 'd3-pro',
    name: 'Fiido D3 Pro',
    subtitle: 'Compact Folding E-Bike',
    price: '$699',
    originalPrice: '$799',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/d3pro-2024-1.jpg',
    badge: 'Sale',
    badgeType: 'sale',
    category: ['all', 'city'],
    features: ['250W Motor', '36V 7.8Ah Battery', 'Foldable Design'],
    productShortName: 'D3 Pro'
  }
])

const filteredProducts = ref(products.value)

const filterByCategory = (categoryId: string) => {
  activeCategory.value = categoryId
  if (categoryId === 'all') {
    filteredProducts.value = products.value
  } else {
    filteredProducts.value = products.value.filter(p => p.category.includes(categoryId))
  }
}

const askAboutProduct = (productName: string) => {
  chatStore.openChat()
  setTimeout(() => {
    const event = new CustomEvent('ask-product', { detail: productName })
    window.dispatchEvent(event)
  }, 300)
}
</script>

<template>
  <section class="products-section" id="products">
    <!-- Section Header -->
    <div class="section-header">
      <span class="section-badge">Our Collection</span>
      <h2 class="section-title">Electric Bikes</h2>
      <p class="section-subtitle">
        Award-winning e-bikes designed for every rider. From city commutes to off-road adventures.
      </p>
    </div>

    <!-- Category Filter -->
    <div class="category-filter">
      <button
        v-for="cat in categories"
        :key="cat.id"
        class="filter-btn"
        :class="{ active: activeCategory === cat.id }"
        @click="filterByCategory(cat.id)"
      >
        {{ cat.name }}
      </button>
    </div>

    <!-- Products Grid -->
    <div class="products-grid">
      <div
        v-for="product in filteredProducts"
        :key="product.id"
        class="product-card"
      >
        <!-- Product Image -->
        <div class="product-image">
          <span
            v-if="product.badge"
            class="product-badge"
            :class="product.badgeType"
          >
            {{ product.badge }}
          </span>
          <img :src="product.image" :alt="product.name">
          <!-- Quick Actions -->
          <div class="quick-actions">
            <button class="action-btn" title="Quick View">
              <svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
            </button>
            <button class="action-btn" @click="askAboutProduct(product.productShortName)" title="Ask AI">
              <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>
            </button>
          </div>
        </div>

        <!-- Product Info -->
        <div class="product-info">
          <span class="product-subtitle">{{ product.subtitle }}</span>
          <h3 class="product-name">{{ product.name }}</h3>

          <!-- Features -->
          <div class="product-features">
            <span v-for="(feature, idx) in product.features" :key="idx" class="feature-tag">
              {{ feature }}
            </span>
          </div>

          <!-- Price & Actions -->
          <div class="product-footer">
            <div class="product-price">
              <span v-if="product.originalPrice" class="original-price">{{ product.originalPrice }}</span>
              <span class="current-price">{{ product.price }}</span>
            </div>
            <div class="product-actions">
              <a href="#" class="btn-shop">Shop Now</a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- View All CTA -->
    <div class="view-all-cta">
      <a href="#" class="btn-view-all">
        View All E-Bikes
        <svg viewBox="0 0 24 24"><path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/></svg>
      </a>
    </div>

    <!-- Features Banner -->
    <div class="features-banner">
      <div class="feature-item">
        <svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l7.59-7.59L21 8l-9 9z"/></svg>
        <div class="feature-text">
          <h4>Free Shipping</h4>
          <p>On all UK orders</p>
        </div>
      </div>
      <div class="feature-item">
        <svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>
        <div class="feature-text">
          <h4>2 Year Warranty</h4>
          <p>Full coverage</p>
        </div>
      </div>
      <div class="feature-item">
        <svg viewBox="0 0 24 24"><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/></svg>
        <div class="feature-text">
          <h4>Best Price</h4>
          <p>Price match guarantee</p>
        </div>
      </div>
      <div class="feature-item">
        <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>
        <div class="feature-text">
          <h4>24/7 Support</h4>
          <p>AI-powered chat</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* =====================================================
   Fiido Official Website Style - Products Section
   - Grid layout with category filter
   - Card hover effects
   - Feature badges
   ===================================================== */

.products-section {
  max-width: 1440px;
  margin: 0 auto;
  padding: 100px 60px;
}

/* Section Header */
.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-badge {
  display: inline-block;
  padding: 8px 20px;
  background: #f5f5f5;
  border-radius: 30px;
  color: #666;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 48px;
  font-weight: 800;
  color: #000;
  margin: 0 0 16px;
  letter-spacing: -1px;
}

.section-subtitle {
  font-size: 18px;
  color: #666;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

/* Category Filter */
.category-filter {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 50px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 12px 24px;
  background: transparent;
  border: 2px solid #e5e5e5;
  border-radius: 30px;
  color: #666;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.filter-btn:hover {
  border-color: #000;
  color: #000;
}

.filter-btn.active {
  background: #000;
  border-color: #000;
  color: #fff;
}

/* Products Grid */
.products-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 30px;
}

/* Product Card */
.product-card {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid #f0f0f0;
}

.product-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
}

/* Product Image */
.product-image {
  position: relative;
  height: 280px;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30px;
  overflow: hidden;
}

.product-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-card:hover .product-image img {
  transform: scale(1.08);
}

/* Product Badge */
.product-badge {
  position: absolute;
  top: 16px;
  left: 16px;
  padding: 6px 14px;
  background: #000;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  z-index: 1;
}

.product-badge.hot {
  background: #ff4757;
}

.product-badge.new {
  background: #2ed573;
}

.product-badge.award {
  background: #ffa502;
  color: #000;
}

.product-badge.sale {
  background: #3742fa;
}

/* Quick Actions */
.quick-actions {
  position: absolute;
  bottom: 16px;
  right: 16px;
  display: flex;
  gap: 8px;
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.3s;
}

.product-card:hover .quick-actions {
  opacity: 1;
  transform: translateY(0);
}

.action-btn {
  width: 40px;
  height: 40px;
  background: #fff;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.action-btn:hover {
  background: #000;
}

.action-btn:hover svg {
  fill: #fff;
}

.action-btn svg {
  width: 20px;
  height: 20px;
  fill: #333;
  transition: fill 0.3s;
}

/* Product Info */
.product-info {
  padding: 24px;
}

.product-subtitle {
  display: block;
  font-size: 12px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.product-name {
  font-size: 20px;
  font-weight: 700;
  color: #000;
  margin: 0 0 16px;
}

/* Product Features */
.product-features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.feature-tag {
  padding: 6px 12px;
  background: #f5f5f5;
  border-radius: 20px;
  font-size: 12px;
  color: #666;
}

/* Product Footer */
.product-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.product-price {
  display: flex;
  align-items: center;
  gap: 10px;
}

.original-price {
  font-size: 14px;
  color: #999;
  text-decoration: line-through;
}

.current-price {
  font-size: 24px;
  font-weight: 700;
  color: #000;
}

.btn-shop {
  padding: 12px 24px;
  background: #000;
  color: #fff;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s;
}

.btn-shop:hover {
  background: #333;
  transform: translateY(-2px);
}

/* View All CTA */
.view-all-cta {
  text-align: center;
  margin-top: 60px;
}

.btn-view-all {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 16px 40px;
  background: transparent;
  color: #000;
  text-decoration: none;
  font-size: 15px;
  font-weight: 600;
  border: 2px solid #000;
  border-radius: 8px;
  transition: all 0.3s;
}

.btn-view-all:hover {
  background: #000;
  color: #fff;
}

.btn-view-all svg {
  width: 20px;
  height: 20px;
  fill: currentColor;
  transition: transform 0.3s;
}

.btn-view-all:hover svg {
  transform: translateX(4px);
}

/* Features Banner */
.features-banner {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 30px;
  margin-top: 100px;
  padding: 40px;
  background: #fafafa;
  border-radius: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.feature-item svg {
  width: 40px;
  height: 40px;
  fill: #000;
  flex-shrink: 0;
}

.feature-text h4 {
  font-size: 15px;
  font-weight: 600;
  color: #000;
  margin: 0 0 4px;
}

.feature-text p {
  font-size: 13px;
  color: #666;
  margin: 0;
}

/* Responsive */
@media (max-width: 1200px) {
  .products-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .features-banner {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .products-section {
    padding: 60px 24px;
  }

  .section-title {
    font-size: 36px;
  }

  .products-grid {
    grid-template-columns: 1fr;
  }

  .category-filter {
    gap: 8px;
  }

  .filter-btn {
    padding: 10px 18px;
    font-size: 13px;
  }

  .features-banner {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .view-all-cta {
    margin-top: 40px;
  }
}
</style>

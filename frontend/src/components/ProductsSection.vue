<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

interface Product {
  name: string
  price: string
  image: string
  badge?: string
  badgeClass?: string
  link: string
  productShortName: string
}

const products = ref<Product[]>([
  {
    name: 'Fiido M1 Pro Fat Tire Electric Bike',
    price: '$1,299',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/7-m1-pro_a8e3269b-7ec7-4f38-a211-1cb2649c18ee_1024x.webp',
    badge: 'Hot',
    badgeClass: 'product-badge hot',
    link: '/products/fiido-m1-pro-fat-tire-electric-bike',
    productShortName: 'M1 Pro'
  },
  {
    name: 'Fiido C11 Pro Electric Commuter Bike',
    price: '$899',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-c11_53e3850d-7074-45b6-9bdb-ca01074b9dda_1024x.webp',
    badge: 'Best Seller',
    badgeClass: 'product-badge',
    link: '/products/fiido-c11-electric-commuter-bike',
    productShortName: 'C11 Pro'
  },
  {
    name: 'Fiido Titan Cargo Electric Bike',
    price: '$1,599',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-titan_1024x.webp',
    badge: 'New',
    badgeClass: 'product-badge new',
    link: '/products/fiido-titan-robust-cargo-electric-bike-with-ul-certified',
    productShortName: 'Titan'
  },
  {
    name: 'Fiido Air Carbon Fiber Electric Bike',
    price: '$2,499',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/c31-img-1_1024x.webp',
    badge: 'Premium',
    badgeClass: 'product-badge hot',
    link: '/products/fiido-air-carbon-fiber-electric-bike',
    productShortName: 'Air'
  }
])

const askAboutProduct = (productName: string) => {
  chatStore.openChat()
  // Wait for chat panel to open
  setTimeout(() => {
    // Trigger message about product
    // This would be handled in ChatPanel component
    const event = new CustomEvent('ask-product', { detail: productName })
    window.dispatchEvent(event)
  }, 300)
}
</script>

<template>
  <section class="products-section" id="products">
    <h2 class="section-title">Featured E-Bikes</h2>
    <div class="products-grid">
      <div
        v-for="(product, index) in products"
        :key="index"
        class="product-card"
      >
        <div class="product-image">
          <span v-if="product.badge" :class="product.badgeClass">{{ product.badge }}</span>
          <img :src="product.image" :alt="product.name">
        </div>
        <div class="product-info">
          <h3 class="product-name">{{ product.name }}</h3>
          <div class="product-price">{{ product.price }}</div>
          <div class="product-actions">
            <button class="btn btn-small btn-secondary" @click="askAboutProduct(product.productShortName)">
              咨询客服
            </button>
            <a :href="product.link" class="btn btn-small">View Details</a>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.products-section {
  max-width: 1400px;
  margin: 80px auto;
  padding: 0 40px;
}

.section-title {
  text-align: center;
  font-size: 42px;
  font-weight: 700;
  margin-bottom: 60px;
  color: #1a1a1a;
  letter-spacing: -0.5px;
  position: relative;
  padding-bottom: 20px;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 4px;
  background: linear-gradient(90deg, #333 0%, #555 100%);
  border-radius: 2px;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
}

.product-card {
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
  cursor: pointer;
}

.product-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-3px);
}

.product-image {
  width: 100%;
  height: 320px;
  background: #f8f8f8;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 20px;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: transform 0.3s;
}

.product-card:hover .product-image img {
  transform: scale(1.05);
}

.product-info {
  padding: 25px 20px;
}

.product-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
  color: #000;
  line-height: 1.4;
  min-height: 44px;
}

.product-price {
  font-size: 24px;
  font-weight: 700;
  color: #000;
  margin-bottom: 18px;
}

.product-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.btn {
  display: inline-block;
  padding: 14px 36px;
  background: #1a1a1a;
  color: #fff;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 600;
  transition: all 0.3s;
  border: none;
  cursor: pointer;
  font-size: 15px;
  letter-spacing: 0.3px;
  text-align: center;
  font-family: 'Montserrat', sans-serif;
}

.btn:hover {
  background: #333;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.btn-small {
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  text-align: center;
  line-height: 1.2;
  border-radius: 4px;
}

.btn-secondary {
  background: #1a1a1a;
  color: #fff;
}

.btn-secondary:hover {
  background: #333;
}

.product-badge {
  position: absolute;
  top: 15px;
  right: 15px;
  background: #d32f2f;
  color: white;
  padding: 5px 12px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.product-badge.hot {
  background: #ff6b35;
}

.product-badge.new {
  background: #4caf50;
}

/* Responsive */
@media (max-width: 768px) {
  .section-title {
    font-size: 32px;
  }
  .products-grid {
    grid-template-columns: 1fr;
  }
}
</style>

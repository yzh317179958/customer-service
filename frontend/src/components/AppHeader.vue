<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

const megaMenus = ref({
  electricBikes: false,
  eBikeGift: false
})

const products = {
  electricBikes: [
    {
      badge: 'Hot',
      badgeClass: 'mega-menu-badge',
      image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-titan_1024x.webp',
      name: 'Fiido Titan Cargo E-Bike',
      price: '$1,599'
    },
    {
      badge: 'New',
      badgeClass: 'mega-menu-badge',
      image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/7-m1-pro_a8e3269b-7ec7-4f38-a211-1cb2649c18ee_1024x.webp',
      name: 'Fiido M1 Pro E-Bike',
      price: '$1,299'
    },
    {
      badge: '',
      badgeClass: '',
      image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-c11_53e3850d-7074-45b6-9bdb-ca01074b9dda_1024x.webp',
      name: 'Fiido C11 Pro Commuter',
      price: '$899'
    },
    {
      badge: 'Premium',
      badgeClass: 'mega-menu-badge',
      image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/c31-img-1_1024x.webp',
      name: 'Fiido Air Carbon Fiber',
      price: '$2,499'
    }
  ],
  gifts: [
    {
      badge: 'Gift',
      badgeClass: 'mega-menu-badge',
      image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-c11_53e3850d-7074-45b6-9bdb-ca01074b9dda_1024x.webp',
      name: 'C11 Gift Package',
      price: '$999'
    },
    {
      badge: '',
      badgeClass: '',
      image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/7-m1-pro_a8e3269b-7ec7-4f38-a211-1cb2649c18ee_1024x.webp',
      name: 'M1 Pro Holiday Set',
      price: '$1,399'
    }
  ]
}

const handleContactClick = () => {
  chatStore.openChat()
}
</script>

<template>
  <header>
    <div class="header-container">
      <a href="/" class="logo">FIIDO</a>
      <nav>
        <div
          class="nav-item"
          @mouseenter="megaMenus.electricBikes = true"
          @mouseleave="megaMenus.electricBikes = false"
        >
          Electric Bikes
          <div class="mega-menu" :class="{ show: megaMenus.electricBikes }">
            <div class="mega-menu-content">
              <div class="mega-menu-left">
                <ul class="mega-menu-categories">
                  <li><a href="#products">Best Sellers E-Bike</a></li>
                  <li><a href="#products">Touring E-Bike</a></li>
                  <li><a href="#products">Cargo E-Bike</a></li>
                  <li><a href="#products">Carbon Fiber E-Bike</a></li>
                  <li><a href="#products">City E-Bike</a></li>
                  <li><a href="#products">Folding E-Bike</a></li>
                  <li><a href="#products">Mini & Small E-Bike</a></li>
                  <li><a href="#products">Launching Soon</a></li>
                </ul>
              </div>
              <div class="mega-menu-right">
                <div
                  v-for="(product, index) in products.electricBikes"
                  :key="index"
                  class="mega-menu-product"
                >
                  <span v-if="product.badge" :class="product.badgeClass">{{ product.badge }}</span>
                  <div class="mega-menu-product-img">
                    <img :src="product.image" :alt="product.name">
                  </div>
                  <div class="mega-menu-product-name">{{ product.name }}</div>
                  <div class="mega-menu-product-price">{{ product.price }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div
          class="nav-item"
          @mouseenter="megaMenus.eBikeGift = true"
          @mouseleave="megaMenus.eBikeGift = false"
        >
          E-Bike Gift
          <div class="mega-menu" :class="{ show: megaMenus.eBikeGift }">
            <div class="mega-menu-content">
              <div class="mega-menu-left">
                <ul class="mega-menu-categories">
                  <li><a href="#products">Holiday Season Sale</a></li>
                  <li><a href="#products">Gift Cards</a></li>
                  <li><a href="#products">Special Bundles</a></li>
                  <li><a href="#products">Accessories Sets</a></li>
                </ul>
              </div>
              <div class="mega-menu-right">
                <div
                  v-for="(product, index) in products.gifts"
                  :key="index"
                  class="mega-menu-product"
                >
                  <span v-if="product.badge" :class="product.badgeClass">{{ product.badge }}</span>
                  <div class="mega-menu-product-img">
                    <img :src="product.image" :alt="product.name">
                  </div>
                  <div class="mega-menu-product-name">{{ product.name }}</div>
                  <div class="mega-menu-product-price">{{ product.price }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <a href="#products">Accessories</a>
        <a href="#about">About</a>
        <a href="#support">Support</a>
        <a href="#" @click.prevent="handleContactClick">Contact</a>
      </nav>
      <div class="header-icons">
        <!-- Search Icon -->
        <div class="header-icon">
          <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
        </div>
        <!-- User Icon -->
        <div class="header-icon">
          <svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
        </div>
        <!-- Cart Icon -->
        <div class="header-icon">
          <svg viewBox="0 0 24 24"><path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/></svg>
          <span class="cart-badge">2</span>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
header {
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 15px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  font-size: 28px;
  font-weight: 700;
  color: #000;
  text-decoration: none;
}

nav {
  display: flex;
  gap: 35px;
  position: relative;
}

nav a,
nav .nav-item {
  color: #000;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s;
  cursor: pointer;
  position: relative;
  padding: 8px 0;
}

nav a:hover,
nav .nav-item:hover {
  color: #1a1a1a;
}

.header-icons {
  display: flex;
  gap: 25px;
  align-items: center;
}

.header-icon {
  width: 24px;
  height: 24px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.header-icon:hover {
  transform: scale(1.1);
}

.header-icon svg {
  width: 100%;
  height: 100%;
  fill: #000;
}

.header-icon:hover svg {
  fill: #1a1a1a;
}

.cart-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #ff4757;
  color: white;
  font-size: 10px;
  font-weight: 700;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Mega Menu */
.mega-menu {
  position: fixed;
  top: 76px;
  left: 0;
  right: 0;
  width: 100vw;
  background: #fff;
  box-shadow: 0 10px 40px rgba(0,0,0,0.15);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1000;
}

.mega-menu.show {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.mega-menu-content {
  max-width: 1600px;
  margin: 0 auto;
  padding: 50px 60px;
  display: flex;
  gap: 60px;
}

.mega-menu-left {
  flex: 0 0 220px;
  border-right: 1px solid #e0e0e0;
  padding-right: 30px;
}

.mega-menu-categories {
  list-style: none;
}

.mega-menu-categories li {
  margin-bottom: 12px;
}

.mega-menu-categories a {
  display: block;
  padding: 10px 15px;
  border-radius: 6px;
  transition: all 0.2s;
  font-size: 14px;
  font-weight: 500;
}

.mega-menu-categories a:hover {
  background: #f5f5f5;
  color: #1a1a1a;
  padding-left: 20px;
}

.mega-menu-right {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 30px;
}

.mega-menu-product {
  text-align: center;
  padding: 0;
  border-radius: 0;
  transition: all 0.3s;
  background: transparent;
}

.mega-menu-product:hover {
  transform: translateY(-5px);
}

.mega-menu-product-img {
  width: 100%;
  height: 280px;
  background: #f8f8f8;
  border-radius: 0;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.mega-menu-product-img img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 20px;
  transition: transform 0.3s;
}

.mega-menu-product:hover .mega-menu-product-img img {
  transform: scale(1.05);
}

.mega-menu-product-name {
  font-size: 14px;
  font-weight: 500;
  color: #000;
  margin-bottom: 8px;
  line-height: 1.4;
}

.mega-menu-product-price {
  font-size: 16px;
  font-weight: 600;
  color: #000;
}

.mega-menu-badge {
  display: inline-block;
  background: #d32f2f;
  color: white;
  font-size: 10px;
  padding: 4px 10px;
  border-radius: 3px;
  margin-bottom: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Responsive */
@media (max-width: 768px) {
  nav {
    display: none;
  }
  .nav-item {
    display: none;
  }
  .mega-menu {
    display: none;
  }
  .header-container {
    padding: 12px 20px;
  }
}

@media (min-width: 769px) and (max-width: 1200px) {
  .mega-menu-content {
    padding: 30px;
  }
  .mega-menu-right {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>

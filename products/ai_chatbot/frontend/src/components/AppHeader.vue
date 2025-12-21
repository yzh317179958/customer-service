<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

const megaMenus = ref({
  electricBikes: false,
  accessories: false
})

const isScrolled = ref(false)
const isMobileMenuOpen = ref(false)

// 产品数据 - 复刻Fiido官网风格
const products = {
  electricBikes: [
    {
      category: 'Best Sellers',
      items: [
        {
          badge: 'Hot',
          image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-titan_1024x.webp',
          name: 'Fiido Titan',
          subtitle: 'Cargo E-Bike',
          price: 'From $1,599'
        },
        {
          badge: 'New',
          image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/7-m1-pro_a8e3269b-7ec7-4f38-a211-1cb2649c18ee_1024x.webp',
          name: 'Fiido M1 Pro',
          subtitle: 'Fat Tire E-Bike',
          price: 'From $1,299'
        },
        {
          badge: '',
          image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-c11-pro_dce92f31-e919-4a94-b8b0-f9cb9b037d75_1024x.webp',
          name: 'Fiido C11 Pro',
          subtitle: 'City Commuter',
          price: 'From $899'
        },
        {
          badge: 'Award',
          image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/c31-img-1_1024x.webp',
          name: 'Fiido Air',
          subtitle: 'Carbon Fiber',
          price: 'From $2,499'
        }
      ]
    }
  ],
  categories: [
    { name: 'All Electric Bikes', link: '#products' },
    { name: 'City & Commuter', link: '#products' },
    { name: 'Cargo & Utility', link: '#products' },
    { name: 'Fat Tire & Off-Road', link: '#products' },
    { name: 'Folding E-Bikes', link: '#products' },
    { name: 'Carbon Fiber Series', link: '#products' }
  ]
}

const handleContactClick = () => {
  chatStore.openChat()
  closeMobileMenu()
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

// 监听滚动
const handleScroll = () => {
  isScrolled.value = window.scrollY > 20
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <!-- Top Banner - Fiido Style -->
  <div class="top-banner">
    <div class="banner-content">
      <span class="banner-text">🚴 Free Shipping on All E-Bikes | 2-Year Warranty</span>
      <a href="#" class="banner-link">Shop Now →</a>
    </div>
  </div>

  <!-- Main Header -->
  <header :class="{ scrolled: isScrolled }">
    <div class="header-container">
      <!-- Logo -->
      <a href="/" class="logo">
        <span class="logo-text">FIIDO</span>
      </a>

      <!-- Desktop Navigation -->
      <nav class="desktop-nav">
        <div
          class="nav-item has-dropdown"
          @mouseenter="megaMenus.electricBikes = true"
          @mouseleave="megaMenus.electricBikes = false"
        >
          <span class="nav-link">
            Electric Bikes
            <svg class="dropdown-arrow" viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg>
          </span>

          <!-- Mega Menu - Fiido Style -->
          <div class="mega-menu" :class="{ show: megaMenus.electricBikes }">
            <div class="mega-menu-inner">
              <div class="mega-menu-left">
                <h4 class="mega-menu-title">Categories</h4>
                <ul class="mega-menu-categories">
                  <li v-for="cat in products.categories" :key="cat.name">
                    <a :href="cat.link">
                      {{ cat.name }}
                      <svg viewBox="0 0 24 24"><path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/></svg>
                    </a>
                  </li>
                </ul>
                <a href="#products" class="view-all-link">View All E-Bikes →</a>
              </div>
              <div class="mega-menu-right">
                <h4 class="mega-menu-title">Featured Products</h4>
                <div class="mega-menu-products">
                  <div
                    v-for="item in products.electricBikes[0]?.items ?? []"
                    :key="item.name"
                    class="mega-product-card"
                  >
                    <div class="mega-product-image">
                      <span v-if="item.badge" class="mega-product-badge">{{ item.badge }}</span>
                      <img :src="item.image" :alt="item.name">
                    </div>
                    <div class="mega-product-info">
                      <h5 class="mega-product-name">{{ item.name }}</h5>
                      <p class="mega-product-subtitle">{{ item.subtitle }}</p>
                      <span class="mega-product-price">{{ item.price }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <a href="#products" class="nav-link">Accessories</a>
        <a href="#about" class="nav-link">About</a>
        <a href="#support" class="nav-link">Support</a>
      </nav>

      <!-- Header Actions -->
      <div class="header-actions">
        <!-- Search -->
        <button class="action-btn" title="Search">
          <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
        </button>

        <!-- Account -->
        <button class="action-btn" title="Account">
          <svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
        </button>

        <!-- Cart -->
        <button class="action-btn cart-btn" title="Cart">
          <svg viewBox="0 0 24 24"><path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/></svg>
          <span class="cart-count">0</span>
        </button>

        <!-- Contact Button -->
        <button class="contact-btn" @click="handleContactClick">
          <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>
          <span>Chat</span>
        </button>

        <!-- Mobile Menu Toggle -->
        <button class="mobile-menu-btn" @click="toggleMobileMenu">
          <span :class="{ active: isMobileMenuOpen }"></span>
        </button>
      </div>
    </div>

    <!-- Mobile Menu -->
    <div class="mobile-menu" :class="{ open: isMobileMenuOpen }">
      <div class="mobile-menu-content">
        <a href="#products" class="mobile-nav-link" @click="closeMobileMenu">Electric Bikes</a>
        <a href="#products" class="mobile-nav-link" @click="closeMobileMenu">Accessories</a>
        <a href="#about" class="mobile-nav-link" @click="closeMobileMenu">About</a>
        <a href="#support" class="mobile-nav-link" @click="closeMobileMenu">Support</a>
        <button class="mobile-contact-btn" @click="handleContactClick">
          Chat with Us
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
/* =====================================================
   Fiido Official Website Style - Header
   - Clean, minimal, modern
   - Black & white primary colors
   - Smooth animations
   ===================================================== */

/* Top Banner */
.top-banner {
  background: #000;
  color: #fff;
  padding: 10px 20px;
  text-align: center;
  font-size: 13px;
}

.banner-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.banner-text {
  font-weight: 400;
}

.banner-link {
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  transition: opacity 0.2s;
}

.banner-link:hover {
  opacity: 0.8;
}

/* Main Header */
header {
  background: #fff;
  position: sticky;
  top: 0;
  z-index: 100;
  transition: all 0.3s ease;
}

header.scrolled {
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.08);
}

.header-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 40px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* Logo */
.logo {
  text-decoration: none;
  display: flex;
  align-items: center;
}

.logo-text {
  font-size: 28px;
  font-weight: 800;
  color: #000;
  letter-spacing: -1px;
}

/* Desktop Navigation */
.desktop-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-item {
  position: relative;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  color: #000;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s;
  cursor: pointer;
}

.nav-link:hover {
  background: #f5f5f5;
}

.dropdown-arrow {
  width: 18px;
  height: 18px;
  fill: currentColor;
  transition: transform 0.3s;
}

.nav-item:hover .dropdown-arrow {
  transform: rotate(180deg);
}

/* Mega Menu */
.mega-menu {
  position: fixed;
  top: 112px; /* banner height + header height */
  left: 0;
  right: 0;
  background: #fff;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1000;
  border-top: 1px solid #f0f0f0;
}

.mega-menu.show {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.mega-menu-inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 40px;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 60px;
}

.mega-menu-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #888;
  margin-bottom: 20px;
}

/* Categories */
.mega-menu-categories {
  list-style: none;
  padding: 0;
  margin: 0;
}

.mega-menu-categories li {
  margin-bottom: 4px;
}

.mega-menu-categories a {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  color: #000;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s;
}

.mega-menu-categories a:hover {
  background: #f5f5f5;
  padding-left: 20px;
}

.mega-menu-categories svg {
  width: 18px;
  height: 18px;
  fill: #ccc;
  opacity: 0;
  transform: translateX(-8px);
  transition: all 0.2s;
}

.mega-menu-categories a:hover svg {
  opacity: 1;
  transform: translateX(0);
}

.view-all-link {
  display: inline-block;
  margin-top: 24px;
  padding: 12px 24px;
  background: #000;
  color: #fff;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.2s;
}

.view-all-link:hover {
  background: #333;
}

/* Mega Menu Products */
.mega-menu-products {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.mega-product-card {
  background: #fafafa;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
  cursor: pointer;
}

.mega-product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
}

.mega-product-image {
  position: relative;
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: #f5f5f5;
}

.mega-product-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: transform 0.3s;
}

.mega-product-card:hover .mega-product-image img {
  transform: scale(1.05);
}

.mega-product-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: #000;
  color: #fff;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
  text-transform: uppercase;
}

.mega-product-info {
  padding: 16px;
}

.mega-product-name {
  font-size: 15px;
  font-weight: 600;
  color: #000;
  margin: 0 0 4px;
}

.mega-product-subtitle {
  font-size: 13px;
  color: #888;
  margin: 0 0 8px;
}

.mega-product-price {
  font-size: 14px;
  font-weight: 600;
  color: #000;
}

/* Header Actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  position: relative;
}

.action-btn:hover {
  background: #f5f5f5;
}

.action-btn svg {
  width: 22px;
  height: 22px;
  fill: #000;
}

.cart-btn {
  position: relative;
}

.cart-count {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 18px;
  height: 18px;
  background: #000;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Contact Button */
.contact-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-left: 8px;
}

.contact-btn:hover {
  background: #333;
  transform: translateY(-1px);
}

.contact-btn svg {
  width: 18px;
  height: 18px;
  fill: currentColor;
}

/* Mobile Menu Button */
.mobile-menu-btn {
  display: none;
  width: 40px;
  height: 40px;
  background: transparent;
  border: none;
  cursor: pointer;
  position: relative;
}

.mobile-menu-btn span,
.mobile-menu-btn span::before,
.mobile-menu-btn span::after {
  display: block;
  width: 22px;
  height: 2px;
  background: #000;
  border-radius: 2px;
  transition: all 0.3s;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.mobile-menu-btn span {
  top: 50%;
  transform: translate(-50%, -50%);
}

.mobile-menu-btn span::before {
  content: '';
  top: -7px;
}

.mobile-menu-btn span::after {
  content: '';
  top: 7px;
}

.mobile-menu-btn span.active {
  background: transparent;
}

.mobile-menu-btn span.active::before {
  top: 0;
  transform: translateX(-50%) rotate(45deg);
}

.mobile-menu-btn span.active::after {
  top: 0;
  transform: translateX(-50%) rotate(-45deg);
}

/* Mobile Menu */
.mobile-menu {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  transform: translateY(-10px);
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s;
}

.mobile-menu.open {
  transform: translateY(0);
  opacity: 1;
  visibility: visible;
}

.mobile-menu-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mobile-nav-link {
  display: block;
  padding: 16px;
  color: #000;
  text-decoration: none;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  transition: background 0.2s;
}

.mobile-nav-link:hover {
  background: #f5f5f5;
}

.mobile-contact-btn {
  margin-top: 16px;
  padding: 16px;
  background: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.mobile-contact-btn:hover {
  background: #333;
}

/* Responsive */
@media (max-width: 1024px) {
  .mega-menu-products {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .top-banner {
    padding: 8px 16px;
    font-size: 12px;
  }

  .banner-content {
    gap: 12px;
  }

  .header-container {
    padding: 0 20px;
    height: 64px;
  }

  .logo-text {
    font-size: 24px;
  }

  .desktop-nav {
    display: none;
  }

  .mega-menu {
    display: none;
  }

  .action-btn:not(.cart-btn) {
    display: none;
  }

  .contact-btn {
    display: none;
  }

  .mobile-menu-btn {
    display: flex;
  }

  .mobile-menu {
    display: block;
  }
}
</style>

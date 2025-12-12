<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

// 轮播相关
const currentSlide = ref(0)
const slides = [
  {
    title: 'Ride the Revolution',
    subtitle: 'Best Electric Bike Brand',
    description: 'Award-winning e-bikes designed for modern riders. Experience the future of urban mobility.',
    video: 'https://cdn.shopify.com/videos/c/vp/8cfaf3b980ce4c8687089e10f1454658/8cfaf3b980ce4c8687089e10f1454658.HD-1080p-4.8Mbps-61898028.mp4',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/hero-titan.jpg',
    cta: 'Explore E-Bikes',
    link: '#products'
  },
  {
    title: 'Fiido Air',
    subtitle: 'Red Dot Award Winner',
    description: 'Ultra-light 13.75kg carbon fiber frame. Redefining what it means to be lightweight.',
    video: '',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/c31-img-1_1024x.webp',
    cta: 'Discover Air',
    link: '#products'
  },
  {
    title: 'Fiido Titan',
    subtitle: 'Ultimate Cargo E-Bike',
    description: 'First in industry with keyless unlocking. 3-Battery structure for longest range.',
    video: '',
    image: 'https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-titan_1024x.webp',
    cta: 'Shop Titan',
    link: '#products'
  }
]

let slideInterval: number | null = null

const nextSlide = () => {
  currentSlide.value = (currentSlide.value + 1) % slides.length
}

const prevSlide = () => {
  currentSlide.value = (currentSlide.value - 1 + slides.length) % slides.length
}

const goToSlide = (index: number) => {
  currentSlide.value = index
  resetInterval()
}

const resetInterval = () => {
  if (slideInterval) {
    clearInterval(slideInterval)
  }
  slideInterval = window.setInterval(nextSlide, 6000)
}

const handleConsultClick = () => {
  chatStore.openChat()
}

// 当前幻灯片计算属性
const activeSlide = computed(() => slides[currentSlide.value]!)

onMounted(() => {
  slideInterval = window.setInterval(nextSlide, 6000)
})

onUnmounted(() => {
  if (slideInterval) {
    clearInterval(slideInterval)
  }
})
</script>

<template>
  <section class="hero">
    <!-- Background -->
    <div class="hero-background">
      <div
        v-for="(slide, index) in slides"
        :key="index"
        class="hero-slide"
        :class="{ active: currentSlide === index }"
      >
        <video
          v-if="slide.video && currentSlide === index"
          class="slide-video"
          autoplay
          muted
          loop
          playsinline
        >
          <source :src="slide.video" type="video/mp4">
        </video>
        <div
          v-else
          class="slide-image"
          :style="{ backgroundImage: `url(${slide.image})` }"
        ></div>
      </div>
      <div class="hero-overlay"></div>
    </div>

    <!-- Content -->
    <div class="hero-container">
      <div class="hero-content">
        <transition name="fade" mode="out-in">
          <div :key="currentSlide" class="hero-text">
            <span class="hero-badge">{{ activeSlide.subtitle }}</span>
            <h1 class="hero-title">{{ activeSlide.title }}</h1>
            <p class="hero-description">{{ activeSlide.description }}</p>
            <div class="hero-actions">
              <a :href="activeSlide.link" class="btn btn-primary">
                {{ activeSlide.cta }}
                <svg viewBox="0 0 24 24"><path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/></svg>
              </a>
              <button class="btn btn-secondary" @click="handleConsultClick">
                <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>
                Chat Now
              </button>
            </div>
          </div>
        </transition>
      </div>

      <!-- Slide Navigation -->
      <div class="slide-nav">
        <button class="nav-arrow prev" @click="prevSlide">
          <svg viewBox="0 0 24 24"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg>
        </button>
        <div class="slide-dots">
          <button
            v-for="(_, index) in slides"
            :key="index"
            class="dot"
            :class="{ active: currentSlide === index }"
            @click="goToSlide(index)"
          ></button>
        </div>
        <button class="nav-arrow next" @click="nextSlide">
          <svg viewBox="0 0 24 24"><path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/></svg>
        </button>
      </div>

      <!-- Stats -->
      <div class="hero-stats">
        <div class="stat">
          <span class="stat-number">600K+</span>
          <span class="stat-label">Happy Riders</span>
        </div>
        <div class="stat">
          <span class="stat-number">10+</span>
          <span class="stat-label">Design Awards</span>
        </div>
        <div class="stat">
          <span class="stat-number">2 Year</span>
          <span class="stat-label">Warranty</span>
        </div>
      </div>
    </div>

    <!-- Scroll Indicator -->
    <div class="scroll-indicator">
      <span>Scroll to explore</span>
      <div class="scroll-line"></div>
    </div>
  </section>
</template>

<style scoped>
/* =====================================================
   Fiido Official Website Style - Hero Section
   - Full-screen immersive design
   - Video/Image carousel
   - Modern typography
   ===================================================== */

.hero {
  position: relative;
  height: 100vh;
  min-height: 700px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

/* Background */
.hero-background {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.hero-slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 1s ease;
}

.hero-slide.active {
  opacity: 1;
}

.slide-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.slide-image {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to right,
    rgba(0, 0, 0, 0.7) 0%,
    rgba(0, 0, 0, 0.4) 50%,
    rgba(0, 0, 0, 0.2) 100%
  );
}

/* Container */
.hero-container {
  position: relative;
  z-index: 1;
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 60px;
  width: 100%;
}

/* Content */
.hero-content {
  max-width: 640px;
}

.hero-text {
  animation: fadeInUp 0.8s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-badge {
  display: inline-block;
  padding: 8px 20px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 30px;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 24px;
}

.hero-title {
  font-size: 72px;
  font-weight: 800;
  color: #fff;
  line-height: 1.1;
  margin: 0 0 24px;
  letter-spacing: -2px;
}

.hero-description {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.6;
  margin: 0 0 40px;
  max-width: 500px;
}

/* Actions */
.hero-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 16px 32px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 8px;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.3s;
}

.btn svg {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.btn-primary {
  background: #fff;
  color: #000;
}

.btn-primary:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.btn-secondary {
  background: transparent;
  color: #fff;
  border: 2px solid rgba(255, 255, 255, 0.5);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.8);
}

/* Slide Navigation */
.slide-nav {
  position: absolute;
  bottom: 120px;
  left: 60px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-arrow {
  width: 48px;
  height: 48px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.nav-arrow:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.6);
}

.nav-arrow svg {
  width: 24px;
  height: 24px;
  fill: #fff;
}

.slide-dots {
  display: flex;
  gap: 10px;
}

.dot {
  width: 40px;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border: none;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.3s;
}

.dot.active {
  background: #fff;
  width: 60px;
}

.dot:hover:not(.active) {
  background: rgba(255, 255, 255, 0.5);
}

/* Stats */
.hero-stats {
  position: absolute;
  bottom: 120px;
  right: 60px;
  display: flex;
  gap: 48px;
}

.stat {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Scroll Indicator */
.scroll-indicator {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.scroll-indicator span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
  letter-spacing: 2px;
}

.scroll-line {
  width: 1px;
  height: 40px;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.6), transparent);
  animation: scrollPulse 2s ease-in-out infinite;
}

@keyframes scrollPulse {
  0%, 100% {
    opacity: 1;
    height: 40px;
  }
  50% {
    opacity: 0.5;
    height: 60px;
  }
}

/* Fade Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* Responsive */
@media (max-width: 1024px) {
  .hero-title {
    font-size: 56px;
  }

  .hero-stats {
    gap: 32px;
  }

  .stat-number {
    font-size: 28px;
  }
}

@media (max-width: 768px) {
  .hero {
    min-height: 600px;
  }

  .hero-container {
    padding: 0 24px;
  }

  .hero-title {
    font-size: 40px;
    letter-spacing: -1px;
  }

  .hero-description {
    font-size: 16px;
  }

  .hero-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }

  .slide-nav {
    bottom: 100px;
    left: 24px;
    right: 24px;
    justify-content: center;
  }

  .nav-arrow {
    display: none;
  }

  .hero-stats {
    display: none;
  }

  .scroll-indicator {
    display: none;
  }
}
</style>

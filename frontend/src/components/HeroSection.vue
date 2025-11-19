<script setup lang="ts">
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

const handleConsultClick = () => {
  chatStore.openChat()
}
</script>

<template>
  <section class="hero">
    <video class="hero-video" autoplay muted loop playsinline>
      <source src="https://cdn.shopify.com/videos/c/vp/8cfaf3b980ce4c8687089e10f1454658/8cfaf3b980ce4c8687089e10f1454658.HD-1080p-4.8Mbps-61898028.mp4" type="video/mp4">
    </video>
    <div class="hero-overlay"></div>
    <div class="hero-content">
      <h1>Best Electric Bike Brand</h1>
      <p>Beautiful, well-built, incredible e-bike for this price segment. Serving 400,000+ riders.</p>
      <button class="btn" @click="handleConsultClick">咨询客服</button>
      <a href="#products" class="btn btn-outline">View Products</a>
    </div>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  color: #fff;
  padding: 120px 40px 100px;
  text-align: center;
  overflow: hidden;
  min-height: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.4) 100%);
  z-index: 1;
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 1000px;
}

.hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 20% 50%, rgba(0,166,160,0.15) 0%, transparent 50%),
              radial-gradient(circle at 80% 50%, rgba(0,166,160,0.1) 0%, transparent 50%);
  pointer-events: none;
  z-index: 1;
}

.hero h1 {
  font-size: 56px;
  font-weight: 700;
  margin-bottom: 24px;
  letter-spacing: -0.5px;
  position: relative;
  z-index: 1;
}

.hero p {
  font-size: 22px;
  margin-bottom: 40px;
  opacity: 0.95;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
  position: relative;
  z-index: 1;
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
  position: relative;
  z-index: 1;
  font-family: 'Montserrat', sans-serif;
}

.btn:hover {
  background: #333;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.btn-outline {
  background: transparent;
  border: 2px solid #fff;
  margin-left: 15px;
}

.btn-outline:hover {
  background: rgba(255,255,255,0.1);
  border-color: #fff;
}

/* Responsive */
@media (max-width: 768px) {
  .hero h1 {
    font-size: 36px;
  }
  .hero p {
    font-size: 18px;
  }
  .hero {
    padding: 80px 30px 60px;
  }
}
</style>

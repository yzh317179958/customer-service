<script setup lang="ts">
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

const handleContactClick = (e: Event) => {
  e.preventDefault()
  chatStore.openChat()
}
</script>

<template>
  <footer>
    <div class="footer-container">
      <div class="footer-section">
        <h3>Shop</h3>
        <ul>
          <li><a href="#">E-Bikes</a></li>
          <li><a href="#">Accessories</a></li>
          <li><a href="#">Parts</a></li>
          <li><a href="#">Gift Cards</a></li>
        </ul>
      </div>
      <div class="footer-section">
        <h3>Support</h3>
        <ul>
          <li><a href="#" @click="handleContactClick">Contact Us</a></li>
          <li><a href="#">Warranty</a></li>
          <li><a href="#">Shipping</a></li>
          <li><a href="#">Returns</a></li>
        </ul>
      </div>
      <div class="footer-section">
        <h3>Company</h3>
        <ul>
          <li><a href="#">About Us</a></li>
          <li><a href="#">Blog</a></li>
          <li><a href="#">Press</a></li>
          <li><a href="#">Careers</a></li>
        </ul>
      </div>
      <div class="footer-section">
        <h3>Contact</h3>
        <ul>
          <li>Email: service@fiido.com</li>
          <li>Phone: +852 5621 6918</li>
          <li>Hours: Mon-Fri 9AM-10PM GMT+8</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; 2025 Fiido Technology Co., Limited. All rights reserved.</p>
    </div>
  </footer>
</template>

<style scoped>
footer {
  background: #000;
  color: #fff;
  padding: 60px 40px 30px;
  margin-top: 100px;
}

.footer-container {
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 40px;
}

.footer-section h3 {
  margin-bottom: 20px;
  font-size: 18px;
}

.footer-section ul {
  list-style: none;
}

.footer-section ul li {
  margin-bottom: 10px;
}

.footer-section a {
  color: #fff;
  text-decoration: none;
  opacity: 0.8;
  transition: opacity 0.3s;
}

.footer-section a:hover {
  opacity: 1;
}

.footer-bottom {
  max-width: 1400px;
  margin: 40px auto 0;
  padding-top: 20px;
  border-top: 1px solid #333;
  text-align: center;
  opacity: 0.6;
}
</style>

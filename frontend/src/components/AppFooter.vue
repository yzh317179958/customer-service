<script setup lang="ts">
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

const handleContactClick = (e: Event) => {
  e.preventDefault()
  chatStore.openChat()
}

// Footer links data
const footerSections = {
  shop: {
    title: 'Shop',
    links: [
      { name: 'All E-Bikes', href: '#products' },
      { name: 'City & Commuter', href: '#products' },
      { name: 'Cargo & Utility', href: '#products' },
      { name: 'Fat Tire', href: '#products' },
      { name: 'Accessories', href: '#products' },
      { name: 'Parts & Components', href: '#products' }
    ]
  },
  support: {
    title: 'Support',
    links: [
      { name: 'Contact Us', href: '#', action: 'chat' },
      { name: 'Help Center', href: '#support' },
      { name: 'Warranty', href: '#support' },
      { name: 'Shipping Info', href: '#support' },
      { name: 'Returns & Refunds', href: '#support' },
      { name: 'Track Order', href: '#support' }
    ]
  },
  company: {
    title: 'Company',
    links: [
      { name: 'About Fiido', href: '#about' },
      { name: 'Our Story', href: '#about' },
      { name: 'Newsroom', href: '#' },
      { name: 'Careers', href: '#' },
      { name: 'Sustainability', href: '#' },
      { name: 'Partner Program', href: '#' }
    ]
  }
}

// Social media links
const socialLinks = [
  { name: 'Facebook', icon: 'M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z', href: 'https://facebook.com/fiido' },
  { name: 'Instagram', icon: 'M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z', href: 'https://instagram.com/fiido' },
  { name: 'YouTube', icon: 'M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z', href: 'https://youtube.com/fiido' },
  { name: 'Twitter', icon: 'M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z', href: 'https://twitter.com/fiido' }
]
</script>

<template>
  <footer>
    <!-- Main Footer Content -->
    <div class="footer-main">
      <div class="footer-container">
        <!-- Brand Section -->
        <div class="footer-brand">
          <a href="/" class="footer-logo">FIIDO</a>
          <p class="footer-tagline">
            Ride the Revolution. Award-winning electric bikes designed for modern urban mobility.
          </p>
          <!-- Newsletter -->
          <div class="newsletter">
            <h4>Stay Connected</h4>
            <div class="newsletter-form">
              <input type="email" placeholder="Enter your email" class="newsletter-input">
              <button class="newsletter-btn">Subscribe</button>
            </div>
          </div>
          <!-- Social Links -->
          <div class="social-links">
            <a
              v-for="social in socialLinks"
              :key="social.name"
              :href="social.href"
              :title="social.name"
              class="social-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              <svg viewBox="0 0 24 24"><path :d="social.icon"/></svg>
            </a>
          </div>
        </div>

        <!-- Links Sections -->
        <div class="footer-links">
          <!-- Shop -->
          <div class="footer-section">
            <h3>{{ footerSections.shop.title }}</h3>
            <ul>
              <li v-for="link in footerSections.shop.links" :key="link.name">
                <a :href="link.href">{{ link.name }}</a>
              </li>
            </ul>
          </div>

          <!-- Support -->
          <div class="footer-section">
            <h3>{{ footerSections.support.title }}</h3>
            <ul>
              <li v-for="link in footerSections.support.links" :key="link.name">
                <a
                  v-if="link.action === 'chat'"
                  href="#"
                  @click="handleContactClick"
                >{{ link.name }}</a>
                <a v-else :href="link.href">{{ link.name }}</a>
              </li>
            </ul>
          </div>

          <!-- Company -->
          <div class="footer-section">
            <h3>{{ footerSections.company.title }}</h3>
            <ul>
              <li v-for="link in footerSections.company.links" :key="link.name">
                <a :href="link.href">{{ link.name }}</a>
              </li>
            </ul>
          </div>

          <!-- Contact -->
          <div class="footer-section">
            <h3>Contact</h3>
            <ul class="contact-list">
              <li>
                <svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
                <a href="mailto:service@fiido.com">service@fiido.com</a>
              </li>
              <li>
                <svg viewBox="0 0 24 24"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
                <span>+852 5621 6918</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
                <span>Mon-Fri 9AM-10PM GMT+8</span>
              </li>
            </ul>
            <button class="chat-btn" @click="handleContactClick">
              <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>
              Chat with Us
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Bottom -->
    <div class="footer-bottom">
      <div class="footer-container">
        <div class="footer-bottom-content">
          <p class="copyright">
            &copy; 2025 Fiido Technology Co., Limited. All rights reserved.
          </p>
          <div class="footer-bottom-links">
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="#">Cookie Policy</a>
            <a href="#">Sitemap</a>
          </div>
          <div class="payment-methods">
            <span>We Accept:</span>
            <div class="payment-icons">
              <svg viewBox="0 0 38 24"><rect width="38" height="24" rx="3" fill="#1A1F71"/><path d="M15.764 16.235h-2.472l1.547-9.51h2.472l-1.547 9.51zm6.375-9.268c-.49-.182-1.253-.387-2.21-.387-2.438 0-4.156 1.235-4.168 3.007-.024 1.303 1.227 2.03 2.164 2.465.961.446 1.285.741 1.285 1.141-.012.614-.773.896-1.486.896-1.001 0-1.528-.134-2.346-.48l-.32-.147-.35 2.055c.585.26 1.667.485 2.787.497 2.594 0 4.277-1.223 4.301-3.104.012-1.034-.649-1.822-2.078-2.468-.862-.416-1.395-.69-1.395-1.115 0-.374.45-.773 1.432-.773a4.39 4.39 0 011.864.35l.228.103.338-1.97-.246-.07zm6.36-.242h-1.907c-.59 0-1.034.162-1.297.763l-3.67 8.747h2.594l.518-1.423h3.171l.29 1.423h2.282l-1.981-9.51zm-3.05 6.158c.205-.531 1.001-2.577 1.001-2.577-.012.024.205-.543.338-.896l.17.806s.481 2.247.585 2.667h-2.094zM12.004 6.725l-2.426 6.491-.254-1.303c-.45-1.45-1.85-3.02-3.414-3.808l2.21 8.118 2.618-.012 3.888-9.486h-2.622z" fill="#fff"/><path d="M7.434 6.725H3.522l-.034.195c3.109.763 5.165 2.606 6.02 4.82l-.87-4.229c-.147-.59-.581-.763-1.204-.786z" fill="#F9A533"/></svg>
              <svg viewBox="0 0 38 24"><rect width="38" height="24" rx="3" fill="#000"/><circle cx="15" cy="12" r="7" fill="#EB001B"/><circle cx="23" cy="12" r="7" fill="#F79E1B"/><path d="M19 7a7 7 0 000 10 7 7 0 000-10z" fill="#FF5F00"/></svg>
              <svg viewBox="0 0 38 24"><rect width="38" height="24" rx="3" fill="#0E4595"/><path d="M35.255 12.486l-2.93-.807c-.248-.068-.296-.127-.296-.351v-.02c0-.214.097-.351.355-.351h1.838c.2 0 .365.098.365.371v.215h1.403v-.186c0-.947-.71-1.362-1.7-1.362h-2.004c-1.038 0-1.67.562-1.67 1.45v.078c0 .8.376 1.23 1.35 1.485l3.1.82c.2.059.248.117.248.322v.059c0 .254-.117.4-.414.4h-2.112c-.238 0-.404-.107-.404-.39v-.303h-1.414v.293c0 .908.7 1.372 1.76 1.372h2.17c1.038 0 1.67-.562 1.67-1.459v-.107c0-.79-.425-1.186-1.315-1.43z" fill="#fff"/><path d="M15.24 10h-1.5l-1.74 2.963-1.72-2.963h-1.54l2.58 4.39v2.61h1.36v-2.61l2.56-4.39zm9.26 0h-4.5v7h4.5v-1.15h-3.14v-1.9h2.89v-1.15h-2.89v-1.65h3.14V10zm4.44 0h-1.36v7h4.5v-1.15h-3.14V10zm-14.6 0h-1.36v7h1.36v-7z" fill="#fff"/></svg>
              <svg viewBox="0 0 38 24"><rect width="38" height="24" rx="3" fill="#32BBFF"/><path d="M19.5 6.5l-9.5 5.5 9.5 5.5v-11z" fill="#fff"/></svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
/* =====================================================
   Fiido Official Website Style - Footer
   - Dark professional design
   - Multi-column layout
   - Social media integration
   ===================================================== */

footer {
  background: #0a0a0a;
  color: #fff;
  margin-top: 0;
}

.footer-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 60px;
}

/* Main Footer */
.footer-main {
  padding: 80px 0 60px;
}

.footer-main .footer-container {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 80px;
}

/* Brand Section */
.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.footer-logo {
  font-size: 32px;
  font-weight: 800;
  color: #fff;
  text-decoration: none;
  letter-spacing: -1px;
}

.footer-tagline {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.7;
  margin: 0;
}

/* Newsletter */
.newsletter h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 12px;
  color: #fff;
}

.newsletter-form {
  display: flex;
  gap: 0;
}

.newsletter-input {
  flex: 1;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-right: none;
  border-radius: 8px 0 0 8px;
  color: #fff;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
}

.newsletter-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.newsletter-input:focus {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.4);
}

.newsletter-btn {
  padding: 14px 24px;
  background: #fff;
  color: #000;
  border: none;
  border-radius: 0 8px 8px 0;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.newsletter-btn:hover {
  background: #f0f0f0;
}

/* Social Links */
.social-links {
  display: flex;
  gap: 12px;
}

.social-link {
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.social-link:hover {
  background: #fff;
  transform: translateY(-3px);
}

.social-link svg {
  width: 20px;
  height: 20px;
  fill: #fff;
  transition: fill 0.3s;
}

.social-link:hover svg {
  fill: #000;
}

/* Footer Links */
.footer-links {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 40px;
}

.footer-section h3 {
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 24px;
  color: #fff;
}

.footer-section ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.footer-section ul li {
  margin-bottom: 14px;
}

.footer-section a {
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s;
}

.footer-section a:hover {
  color: #fff;
  padding-left: 4px;
}

/* Contact List */
.contact-list li {
  display: flex;
  align-items: center;
  gap: 12px;
}

.contact-list svg {
  width: 18px;
  height: 18px;
  fill: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
}

.contact-list span,
.contact-list a {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  text-decoration: none;
}

.contact-list a:hover {
  color: #fff;
  padding-left: 0;
}

/* Chat Button */
.chat-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  padding: 14px 24px;
  background: #fff;
  color: #000;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.chat-btn:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
}

.chat-btn svg {
  width: 18px;
  height: 18px;
  fill: currentColor;
}

/* Footer Bottom */
.footer-bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 30px 0;
}

.footer-bottom-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px;
}

.copyright {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}

.footer-bottom-links {
  display: flex;
  gap: 24px;
}

.footer-bottom-links a {
  color: rgba(255, 255, 255, 0.4);
  text-decoration: none;
  font-size: 13px;
  transition: color 0.3s;
}

.footer-bottom-links a:hover {
  color: #fff;
}

/* Payment Methods */
.payment-methods {
  display: flex;
  align-items: center;
  gap: 12px;
}

.payment-methods span {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

.payment-icons {
  display: flex;
  gap: 8px;
}

.payment-icons svg {
  height: 24px;
  width: auto;
  border-radius: 4px;
}

/* Responsive */
@media (max-width: 1200px) {
  .footer-main .footer-container {
    grid-template-columns: 1fr;
    gap: 60px;
  }

  .footer-links {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1024px) {
  .footer-links {
    grid-template-columns: repeat(2, 1fr);
    gap: 40px 60px;
  }
}

@media (max-width: 768px) {
  .footer-container {
    padding: 0 24px;
  }

  .footer-main {
    padding: 60px 0 40px;
  }

  .footer-links {
    grid-template-columns: 1fr;
    gap: 32px;
  }

  .footer-section h3 {
    margin-bottom: 16px;
  }

  .footer-bottom-content {
    flex-direction: column;
    text-align: center;
  }

  .footer-bottom-links {
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
  }

  .payment-methods {
    flex-direction: column;
    gap: 8px;
  }
}
</style>

/* =============================================
   MANIKANDAPRABU VK — PORTFOLIO JAVASCRIPT
   ============================================= */

// ── Particle System ──
(function initParticles() {
  const canvas = document.getElementById('particles-canvas');
  const ctx = canvas.getContext('2d');
  let particles = [];
  let animId;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  function createParticle() {
    return {
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      radius: Math.random() * 1.5 + 0.5,
      opacity: Math.random() * 0.5 + 0.1,
      color: Math.random() > 0.5 ? '139,107,67' : '60,62,68'
    };
  }

  for (let i = 0; i < 100; i++) particles.push(createParticle());

  function drawConnections() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 140) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(139,107,67,${0.08 * (1 - dist / 140)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawConnections();
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.color},${p.opacity})`;
      ctx.fill();
    });
    animId = requestAnimationFrame(animate);
  }
  animate();
})();

// ── Navbar Scroll Effect ──
(function initNavbar() {
  const navbar = document.getElementById('navbar');
  let lastScroll = 0;

  window.addEventListener('scroll', () => {
    const currentScroll = window.scrollY;
    if (currentScroll > 80) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
    lastScroll = currentScroll;
  }, { passive: true });
})();

// ── Mobile Menu ──
(function initMobileMenu() {
  const hamburger = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobile-menu');
  const mobileLinks = document.querySelectorAll('.mobile-link');

  function toggleMenu() {
    const isOpen = mobileMenu.classList.toggle('active');
    document.body.style.overflow = isOpen ? 'hidden' : '';
    const spans = hamburger.querySelectorAll('span');
    if (isOpen) {
      spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
      spans[1].style.opacity = '0';
      spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
    } else {
      spans[0].style.transform = '';
      spans[1].style.opacity = '';
      spans[2].style.transform = '';
    }
  }

  hamburger.addEventListener('click', toggleMenu);
  mobileLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (mobileMenu.classList.contains('active')) toggleMenu();
    });
  });
})();

// ── Typewriter Effect ──
(function initTypewriter() {
  const el = document.getElementById('typewriter');
  if (!el) return;
  const phrases = [
    'ML Systems',
    'Data Pipelines',
    'Stock Predictors',
    'Flask APIs',
    'React Apps',
    'Power BI Dashboards',
    'AI Solutions'
  ];
  let phraseIdx = 0;
  let charIdx = 0;
  let deleting = false;
  let pause = false;

  function type() {
    if (pause) { setTimeout(type, 1500); pause = false; return; }
    const current = phrases[phraseIdx];

    if (!deleting) {
      el.textContent = current.substring(0, charIdx + 1);
      charIdx++;
      if (charIdx === current.length) { deleting = true; pause = true; }
      setTimeout(type, 100);
    } else {
      el.textContent = current.substring(0, charIdx - 1);
      charIdx--;
      if (charIdx === 0) {
        deleting = false;
        phraseIdx = (phraseIdx + 1) % phrases.length;
      }
      setTimeout(type, 55);
    }
  }

  setTimeout(type, 800);
})();

// ── Scroll Reveal ──
(function initReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -60px 0px' });

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
})();

// ── Counter Animation ──
(function initCounters() {
  const counters = document.querySelectorAll('.stat-num[data-target]');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !entry.target.dataset.counted) {
        entry.target.dataset.counted = 'true';
        const target = parseInt(entry.target.dataset.target);
        let count = 0;
        const step = target / 40;
        const interval = setInterval(() => {
          count = Math.min(count + step, target);
          entry.target.textContent = Math.floor(count) + '+';
          if (count >= target) clearInterval(interval);
        }, 40);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(c => observer.observe(c));
})();

// ── Active Nav Link on Scroll ──
(function initActiveNav() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === '#' + id) {
            link.classList.add('active');
          }
        });
      }
    });
  }, { threshold: 0.4 });

  sections.forEach(s => observer.observe(s));
})();

// ── Smooth Scroll for all anchor links ──
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    const href = this.getAttribute('href');
    if (href === '#') return;
    const target = document.querySelector(href);
    if (target) {
      e.preventDefault();
      const offset = 80;
      const top = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  });
});



// ── Cursor Glow Effect on Mouse Move ──
(function initCursorGlow() {
  const glow = document.createElement('div');
  glow.style.cssText = `
    position:fixed; pointer-events:none; z-index:9999;
    width:350px; height:350px; border-radius:50%;
    background:radial-gradient(circle, rgba(139,107,67,0.05) 0%, transparent 70%);
    transform:translate(-50%,-50%);
    transition:transform 0.1s linear;
    top:-175px; left:-175px;
  `;
  document.body.appendChild(glow);

  window.addEventListener('mousemove', (e) => {
    glow.style.left = e.clientX + 'px';
    glow.style.top = e.clientY + 'px';
  }, { passive: true });
})();

// ── Project Card Tilt on Hover ──
(function initCardTilt() {
  document.querySelectorAll('.project-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const midX = rect.width / 2;
      const midY = rect.height / 2;
      const rotX = ((y - midY) / midY) * -3;
      const rotY = ((x - midX) / midX) * 3;
      card.style.transform = `perspective(1000px) rotateX(${rotX}deg) rotateY(${rotY}deg)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });
})();

// ── Fresco Parallax & Fluid Reveal Effect ──
(function initFrescoEffects() {
  const canvas = document.getElementById('fresco-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // Offscreen mask canvas (white shapes = where color bleeds through)
  const maskCanvas = document.createElement('canvas');
  const maskCtx = maskCanvas.getContext('2d');

  // Offscreen composition canvas for color stamp
  const stampCanvas = document.createElement('canvas');
  const stampCtx = stampCanvas.getContext('2d');

  let imageLoaded = false;
  const imgColor = new Image();
  const grayscaleCanvas = document.createElement('canvas');
  const grayscaleCtx = grayscaleCanvas.getContext('2d');

  imgColor.onload = () => {
    grayscaleCanvas.width = imgColor.width;
    grayscaleCanvas.height = imgColor.height;
    grayscaleCtx.filter = 'grayscale(100%) contrast(105%) brightness(110%)';
    grayscaleCtx.drawImage(imgColor, 0, 0);
    grayscaleCtx.filter = 'none';
    imageLoaded = true;
  };
  imgColor.src = 'background.jpg';

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    maskCanvas.width = canvas.width;
    maskCanvas.height = canvas.height;
    stampCanvas.width = canvas.width;
    stampCanvas.height = canvas.height;
  }
  resize();
  window.addEventListener('resize', resize);

  // Subtle parallax on mouse move
  window.addEventListener('mousemove', (e) => {
    const xVal = (e.clientX - window.innerWidth / 2) * -0.010;
    const yVal = (e.clientY - window.innerHeight / 2) * -0.010;
    canvas.style.transform = `scale(1.03) translate(${xVal}px, ${yVal}px)`;
  }, { passive: true });

  // ── Paint Stroke Particle ──
  // Each particle is a blob of "color window" that fades over time
  class PaintStroke {
    constructor(x, y, vx, vy, size, speed) {
      this.x = x;
      this.y = y;
      this.vx = vx;
      this.vy = vy;
      this.baseRadius = size;
      this.radius = size;
      // Slower decay = longer lasting trails
      this.life = 1.0;
      this.decay = 0.004 + Math.random() * 0.008;
      this.angle = Math.atan2(vy, vx);
      this.spin = (Math.random() - 0.5) * 0.04;
      this.speed = speed;
    }

    update() {
      // Friction
      this.vx *= 0.97;
      this.vy *= 0.97;

      // Curl turbulence — organic swirling
      const t = Date.now() * 0.0007;
      this.vx += Math.sin(this.y * 0.006 + t) * 0.15;
      this.vy += Math.cos(this.x * 0.006 + t) * 0.15;

      this.x += this.vx;
      this.y += this.vy;
      this.angle += this.spin;

      // Blob expands as it fades — like ink blooming in water
      this.radius = this.baseRadius * (1.0 + (1.0 - this.life) * 0.8);
      this.life -= this.decay;
    }

    draw(ctx) {
      const alpha = this.life * this.life; // ease-out the fade
      if (alpha <= 0.01) return;

      // Elongated brush stroke shape
      const stretchX = this.vx * 2.0;
      const stretchY = this.vy * 2.0;

      const grad = ctx.createRadialGradient(
        this.x - stretchX, this.y - stretchY, this.radius * 0.05,
        this.x, this.y, this.radius
      );
      grad.addColorStop(0,   `rgba(255,255,255,${alpha})`);
      grad.addColorStop(0.3, `rgba(255,255,255,${alpha * 0.7})`);
      grad.addColorStop(0.7, `rgba(255,255,255,${alpha * 0.2})`);
      grad.addColorStop(1,   'rgba(255,255,255,0)');

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fill();

      // Sub-vortex droplets for organic ink-drag look
      for (let i = 0; i < 4; i++) {
        const subAngle = this.angle + i * (Math.PI / 2) + Date.now() * 0.0003;
        const dist = this.radius * 0.5 * (1.2 - this.life);
        const sx = this.x + Math.cos(subAngle) * dist;
        const sy = this.y + Math.sin(subAngle) * dist;
        const sr = this.radius * 0.38;

        const sg = ctx.createRadialGradient(sx, sy, 0, sx, sy, sr);
        sg.addColorStop(0, `rgba(255,255,255,${alpha * 0.45})`);
        sg.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = sg;
        ctx.beginPath();
        ctx.arc(sx, sy, sr, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  let particles = [];
  let lastX = null;
  let lastY = null;

  function handlePointerMove(px, py) {
    if (lastX === null) { lastX = px; lastY = py; return; }

    const dx = px - lastX;
    const dy = py - lastY;
    const speed = Math.sqrt(dx * dx + dy * dy);

    // Only fire on real movement — prevents static/dusty idle artefacts
    if (speed > 2.0) {
      const steps = Math.min(Math.ceil(speed / 6), 12);
      for (let i = 0; i < steps; i++) {
        const t = i / steps;
        const x = lastX + dx * t;
        const y = lastY + dy * t;
        const sz = Math.max(55, Math.min(180, speed * 3.2));
        const vx = (dx / speed) * speed * 0.09 + (Math.random() - 0.5) * 1.0;
        const vy = (dy / speed) * speed * 0.09 + (Math.random() - 0.5) * 1.0;
        particles.push(new PaintStroke(x, y, vx, vy, sz, speed));
      }
    }

    lastX = px;
    lastY = py;
  }

  window.addEventListener('mousemove', (e) => handlePointerMove(e.clientX, e.clientY), { passive: true });
  window.addEventListener('mouseleave', () => { lastX = null; lastY = null; });
  window.addEventListener('touchmove', (e) => {
    if (e.touches.length > 0) handlePointerMove(e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });
  window.addEventListener('touchend', () => { lastX = null; lastY = null; });

  // Draw image cover-fit helper
  function drawCover(targetCtx, src, alpha) {
    targetCtx.globalAlpha = alpha;
    const cw = canvas.width, ch = canvas.height;
    const iw = src.width,   ih = src.height;
    const cAR = cw / ch, iAR = iw / ih;
    let dw, dh, dx, dy;
    if (cAR > iAR) { dw = cw; dh = cw / iAR; dx = 0; dy = (ch - dh) / 2; }
    else            { dh = ch; dw = ch * iAR;  dy = 0; dx = (cw - dw) / 2; }
    targetCtx.drawImage(src, dx, dy, dw, dh);
    targetCtx.globalAlpha = 1.0;
  }

  let currentBaseOpacity = 0.15;

  function tick() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!imageLoaded) {
      ctx.fillStyle = '#f5f4f0';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      requestAnimationFrame(tick);
      return;
    }

    // Determine target opacity based on whether there's an active hover trail
    const targetOpacity = particles.length > 0 ? 0.35 : 0.15;
    currentBaseOpacity += (targetOpacity - currentBaseOpacity) * 0.08;

    // ── 1. GRAYSCALE BASE — dynamic subtle opacity ──
    drawCover(ctx, grayscaleCanvas, currentBaseOpacity);

    // ── 2. Build particle mask ──
    maskCtx.clearRect(0, 0, canvas.width, canvas.height);

    // 2. Update and draw particles to offscreen mask
    particles = particles.filter(p => {
      p.update();
      if (p.life > 0) {
        p.draw(maskCtx);
        return true;
      }
      return false;
    });

    // ── 3. Stamp vivid COLOR through particle mask — only where trails exist ──
    if (particles.length > 0) {
      stampCtx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw the white mask blobs onto stampCanvas
      stampCtx.drawImage(maskCanvas, 0, 0);

      // source-in = "stencil" — color image shows ONLY through the white blobs
      stampCtx.globalCompositeOperation = 'source-in';
      drawCover(stampCtx, imgColor, 0.7); // 0.7 so it's "seeable but not solidly seeable"
      stampCtx.globalCompositeOperation = 'source-over';

      // Overlay vivid color stamp on top of grayscale base
      ctx.drawImage(stampCanvas, 0, 0);
    }

    requestAnimationFrame(tick);
  }
  tick();
})();

// ── Add active nav style ──
const style = document.createElement('style');
style.textContent = `.nav-link.active { color: var(--text-primary) !important; background: rgba(255,255,255,0.05) !important; }`;
document.head.appendChild(style);

// ── Console greeting for devs ──
console.log(
  '%c🚀 Manikandaprabu VK — Portfolio',
  'color: #c5a880; font-size: 16px; font-weight: bold; font-family: monospace;'
);
console.log(
  '%cLooking to hire? Reach me at manikandaprabuvk@gmail.com',
  'color: rgba(255,255,255,0.5); font-size: 12px; font-family: monospace;'
);

// ── Premium Custom Cursor & Magnetic Antigravity Effects ──
(function initMagneticEffects() {
  // Ensure GSAP is loaded
  if (typeof gsap === 'undefined') return;

  const cursorDot = document.querySelector('.cursor-dot');
  
  if (!cursorDot) return;

  let isCursorVisible = false;
  let mouseX = window.innerWidth / 2;
  let mouseY = window.innerHeight / 2;

  window.addEventListener('mousemove', (e) => {
    if (!document.body.classList.contains('hide-cursor')) {
      document.body.classList.add('hide-cursor');
    }
    mouseX = e.clientX;
    mouseY = e.clientY;
    
    if (!isCursorVisible) {
      gsap.to(cursorDot, { opacity: 1, duration: 0.3 });
      isCursorVisible = true;
    }
    
    // Dot follows instantly and stays centered
    gsap.set(cursorDot, { 
      x: mouseX, 
      y: mouseY,
      xPercent: -50,
      yPercent: -50
    });
  }, { passive: true });

  // ── Magnetic Attraction Effect ──
  const magnetics = document.querySelectorAll('a, button, .project-card, .contact-card, .social-btn');
  
  magnetics.forEach(el => {
    el.addEventListener('mouseenter', () => {
      // Optional: scale the dot slightly when hovering
      gsap.to(cursorDot, { scale: 1.5, duration: 0.3 });
    });
    
    el.addEventListener('mouseleave', () => {
      gsap.to(cursorDot, { scale: 1, duration: 0.3 });
      // Spring back to original position using elastic GSAP easing
      gsap.to(el, { x: 0, y: 0, duration: 0.8, ease: 'elastic.out(1, 0.4)' });
    });
    
    el.addEventListener('mousemove', (e) => {
      const rect = el.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      
      const distanceX = e.clientX - centerX;
      const distanceY = e.clientY - centerY;
      
      // Pull element towards cursor (30% of distance)
      gsap.to(el, {
        x: distanceX * 0.3,
        y: distanceY * 0.3,
        duration: 0.4,
        ease: 'power2.out'
      });
    });
  });

  // ── Foreground Parallax Effects ──
  const parallaxElements = document.querySelectorAll('.hero-title, .hero-subtitle, .section-title');
  
  window.addEventListener('mousemove', (e) => {
    // Calculate offset from center of screen
    const x = (e.clientX - window.innerWidth / 2);
    const y = (e.clientY - window.innerHeight / 2);
    
    parallaxElements.forEach(el => {
      // Foreground elements move slightly in same direction (factor 0.02)
      gsap.to(el, {
        x: x * 0.02,
        y: y * 0.02,
        duration: 0.6,
        ease: 'power2.out'
      });
    });
  }, { passive: true });
})();

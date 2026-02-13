/* ============================================================
   AI-Native Interactions — DesignCompare
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initDropZones();
  initFileInputLabels();
  initCollapsibles();
  initScoreBars();
  initFadeIn();
});

/* ============ Particle Background ============ */
function initParticles() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let particles = [];
  let w, h;
  const PARTICLE_COUNT = 60;
  const CONNECTION_DIST = 140;
  let animId;

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }

  function createParticles() {
    particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.8 + 0.5,
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, w, h);

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < CONNECTION_DIST) {
          const alpha = (1 - dist / CONNECTION_DIST) * 0.12;
          ctx.strokeStyle = `rgba(99, 102, 241, ${alpha})`;
          ctx.lineWidth = 0.6;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }

    // Draw particles
    for (const p of particles) {
      ctx.fillStyle = 'rgba(99, 102, 241, 0.4)';
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();

      // Move
      p.x += p.vx;
      p.y += p.vy;

      // Bounce
      if (p.x < 0 || p.x > w) p.vx *= -1;
      if (p.y < 0 || p.y > h) p.vy *= -1;
    }

    animId = requestAnimationFrame(draw);
  }

  // Check prefers-reduced-motion
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  resize();
  createParticles();
  draw();

  window.addEventListener('resize', () => {
    resize();
    createParticles();
  });
}

/* ============ Drop Zone / File Upload ============ */
function initDropZones() {
  document.querySelectorAll('.upload-file-card').forEach(card => {
    const input = card.querySelector('input[type="file"]');
    if (!input) return;

    // Drag events
    card.addEventListener('dragover', (e) => {
      e.preventDefault();
      card.classList.add('drag-over');
    });

    card.addEventListener('dragleave', () => {
      card.classList.remove('drag-over');
    });

    card.addEventListener('drop', (e) => {
      e.preventDefault();
      card.classList.remove('drag-over');
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        // Set file to input
        const dt = new DataTransfer();
        dt.items.add(files[0]);
        input.files = dt.files;
        updateFileCard(card, files[0].name);
      }
    });

    // Native file select
    input.addEventListener('change', () => {
      if (input.files.length > 0) {
        updateFileCard(card, input.files[0].name);
      }
    });
  });
}

function updateFileCard(card, fileName) {
  card.classList.add('has-file');
  let nameEl = card.querySelector('.file-name');
  if (!nameEl) {
    nameEl = document.createElement('div');
    nameEl.className = 'file-name';
    card.appendChild(nameEl);
  }
  nameEl.textContent = fileName;

  // Update icon to checkmark
  const iconSvg = card.querySelector('.file-icon svg');
  if (iconSvg) {
    iconSvg.innerHTML = '<polyline points="20 6 9 17 4 12"></polyline>';
  }
}

/* ============ File Input Labels ============ */
function initFileInputLabels() {
  // For form-group based file inputs
  document.querySelectorAll('.form-group input[type="file"]').forEach(input => {
    input.addEventListener('change', () => {
      const nameDisplay = input.closest('.form-group').querySelector('.file-chosen-name');
      if (nameDisplay && input.files.length > 0) {
        nameDisplay.textContent = input.files[0].name;
        nameDisplay.style.display = 'block';
      }
    });
  });
}

/* ============ Collapsibles ============ */
function initCollapsibles() {
  document.querySelectorAll('.collapsible-toggle').forEach(toggle => {
    toggle.addEventListener('click', () => {
      const parent = toggle.closest('.collapsible');
      parent.classList.toggle('open');
    });
  });
}

/* ============ Score Bars Animation ============ */
function initScoreBars() {
  const bars = document.querySelectorAll('.score-bar-fill');
  if (bars.length === 0) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const fill = entry.target;
        const width = fill.dataset.width || '0%';
        requestAnimationFrame(() => {
          fill.style.width = width;
        });
        observer.unobserve(fill);
      }
    });
  }, { threshold: 0.1 });

  bars.forEach(bar => {
    const targetWidth = bar.style.width || bar.dataset.width;
    bar.dataset.width = targetWidth;
    bar.style.width = '0%';
    observer.observe(bar);
  });
}

/* ============ Fade-In on Scroll ============ */
function initFadeIn() {
  const els = document.querySelectorAll('.animate-in');
  if (els.length === 0) return;

  const maxAnimatedHeight = window.innerHeight * 1.5;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0, rootMargin: '0px 0px -8% 0px' });

  els.forEach(el => {
    // Very tall sections (e.g. large tables) should not be paused,
    // otherwise they may stay invisible while still occupying layout height.
    if (el.offsetHeight > maxAnimatedHeight) {
      el.style.animationPlayState = 'running';
      return;
    }
    el.style.animationPlayState = 'paused';
    observer.observe(el);
  });
}

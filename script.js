/* ═══════════════════════════════════════════════════
   КМ-ИНЖИНИРИНГ — Premium Interactions
   Hero slider, scroll reveal, sticky header, smooth scroll
   ═══════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // ═══════════════════════════════════════════════
  // HERO SLIDER
  // ═══════════════════════════════════════════════

  const heroSlider = (() => {
    const slider = document.getElementById('hero-slider');
    const slides = slider ? slider.querySelectorAll('.hero__slide') : [];
    const dotsContainer = document.getElementById('hero-dots');
    const progressBar = document.getElementById('hero-progress');

    if (slides.length === 0) return;

    let current = 0;
    let interval = null;
    const INTERVAL_MS = 4000;

    // Create dots
    slides.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.classList.add('hero__dot');
      dot.setAttribute('aria-label', `Слайд ${i + 1}`);
      if (i === 0) dot.classList.add('active');
      dot.addEventListener('click', () => {
        goTo(i);
        resetAutoPlay();
      });
      dotsContainer.appendChild(dot);
    });

    const dots = dotsContainer.querySelectorAll('.hero__dot');

    function goTo(index) {
      // Remove active from current
      slides[current].classList.remove('active');
      dots[current].classList.remove('active');

      // Update index
      current = index;

      // Add active to new
      slides[current].classList.add('active');
      dots[current].classList.add('active');

      // Progress bar — 4 second timer animation
      if (progressBar) {
        progressBar.style.transition = 'none';
        progressBar.style.width = '0%';
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            progressBar.style.transition = `width ${INTERVAL_MS}ms linear`;
            progressBar.style.width = '100%';
          });
        });
      }

      // Restart dot progress animation
      dots.forEach(d => {
        d.style.animation = 'none';
        d.offsetHeight; // trigger reflow
        d.style.animation = '';
      });
    }

    function next() {
      goTo((current + 1) % slides.length);
    }

    function startAutoPlay() {
      interval = setInterval(next, INTERVAL_MS);
      // Start initial progress
      if (progressBar) {
        progressBar.style.transition = `width ${INTERVAL_MS}ms linear`;
        progressBar.style.width = '100%';
      }
    }

    function resetAutoPlay() {
      clearInterval(interval);
      startAutoPlay();
    }

    startAutoPlay();

    // Pause on hover
    if (slider) {
      slider.addEventListener('mouseenter', () => clearInterval(interval));
      slider.addEventListener('mouseleave', () => {
        interval = setInterval(next, INTERVAL_MS);
      });
    }

    // Touch / swipe support
    let touchStartX = 0;
    let touchEndX = 0;

    if (slider) {
      slider.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
      }, { passive: true });

      slider.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        const diff = touchStartX - touchEndX;
        if (Math.abs(diff) > 50) {
          if (diff > 0) {
            goTo((current + 1) % slides.length);
          } else {
            goTo((current - 1 + slides.length) % slides.length);
          }
          resetAutoPlay();
        }
      }, { passive: true });
    }
  })();


  // ═══════════════════════════════════════════════
  // SCROLL REVEAL (Intersection Observer)
  // ═══════════════════════════════════════════════

  const scrollReveal = (() => {
    const elements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');

    if (!elements.length) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.15,
      rootMargin: '0px 0px -50px 0px'
    });

    elements.forEach(el => observer.observe(el));
  })();


  // ═══════════════════════════════════════════════
  // STICKY HEADER with backdrop blur
  // ═══════════════════════════════════════════════

  const stickyHeader = (() => {
    const header = document.getElementById('header');
    if (!header) return;

    let lastScrollY = 0;

    const onScroll = () => {
      const scrollY = window.scrollY;

      if (scrollY > 50) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }

      lastScrollY = scrollY;
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll(); // initial check
  })();


  // ═══════════════════════════════════════════════
  // SMOOTH SCROLL for navigation links
  // ═══════════════════════════════════════════════

  const smoothScroll = (() => {
    const links = document.querySelectorAll('[data-nav], [data-mobile-nav]');

    links.forEach(link => {
      link.addEventListener('click', (e) => {
        const href = link.getAttribute('href');
        if (href && href.startsWith('#')) {
          e.preventDefault();
          const target = document.querySelector(href);
          if (target) {
            const headerHeight = document.getElementById('header')?.offsetHeight || 80;
            const top = target.getBoundingClientRect().top + window.scrollY - headerHeight;

            window.scrollTo({
              top: top,
              behavior: 'smooth'
            });

            // Close mobile menu if open
            const mobileMenu = document.getElementById('mobile-menu');
            const burger = document.getElementById('burger');
            if (mobileMenu?.classList.contains('active')) {
              mobileMenu.classList.remove('active');
              burger?.classList.remove('active');
              document.body.style.overflow = '';
            }
          }
        }
      });
    });
  })();


  // ═══════════════════════════════════════════════
  // ACTIVE NAV LINK on scroll
  // ═══════════════════════════════════════════════

  const activeNav = (() => {
    const sections = document.querySelectorAll('.section[id], .cta[id]');
    const navLinks = document.querySelectorAll('.header__nav-link[data-nav]');

    if (!sections.length || !navLinks.length) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute('id');
          navLinks.forEach(link => {
            link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
          });
        }
      });
    }, {
      threshold: 0.3,
      rootMargin: '-80px 0px -50% 0px'
    });

    sections.forEach(section => observer.observe(section));
  })();


  // ═══════════════════════════════════════════════
  // MOBILE BURGER MENU
  // ═══════════════════════════════════════════════

  const burgerMenu = (() => {
    const burger = document.getElementById('burger');
    const mobileMenu = document.getElementById('mobile-menu');

    if (!burger || !mobileMenu) return;

    burger.addEventListener('click', () => {
      const isOpen = burger.classList.toggle('active');
      mobileMenu.classList.toggle('active');
      burger.setAttribute('aria-expanded', isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });
  })();


  // ═══════════════════════════════════════════════
  // CONTACT FORM — basic validation & feedback
  // ═══════════════════════════════════════════════

  // ═══════════════════════════════════════════════
  // CONTACT FORM — FormSubmit.co handles submission
  // ═══════════════════════════════════════════════

  // const contactForm = (() => {
  //   const form = document.getElementById('contact-form');
  //   if (!form) return;

  //   // We let FormSubmit.co handle the submission natively.
  //   // No e.preventDefault() here.
  // })();


  // ═══════════════════════════════════════════════
  // SECTION TITLE ANIMATED UNDERLINE
  // ═══════════════════════════════════════════════

  const animatedSeparators = (() => {
    const separators = document.querySelectorAll('.separator');
    if (!separators.length) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.animation = 'lineGrow 1s ease forwards';
        }
      });
    }, { threshold: 0.5 });

    separators.forEach(sep => observer.observe(sep));
  })();


  // ═══════════════════════════════════════════════
  // PARALLAX on CTA blob decorations
  // ═══════════════════════════════════════════════

  const parallax = (() => {
    const cta = document.querySelector('.cta');
    if (!cta) return;

    window.addEventListener('scroll', () => {
      const rect = cta.getBoundingClientRect();
      const windowH = window.innerHeight;

      if (rect.top < windowH && rect.bottom > 0) {
        const progress = 1 - (rect.top / windowH);
        const yOffset = progress * 40;
        cta.style.setProperty('--parallax-y', `${yOffset}px`);
      }
    }, { passive: true });
  })();
  // ═══════════════════════════════════════════════
  // WORKFLOW STEP ANIMATION — Looping progress
  // ═══════════════════════════════════════════════

  const workflowAnim = (() => {
    const steps = document.querySelectorAll('.workflow-step');
    if (steps.length === 0) return;

    let currentStep = -1;
    let timer = null;
    let isVisible = false;
    const STEP_DURATION = 2000; // ms per step
    const PAUSE_BETWEEN = 1200; // pause before restart

    function clearStates() {
      steps.forEach(step => {
        step.classList.remove('wf-active', 'wf-done');
      });
    }

    function setStep(index) {
      // Clear all first
      steps.forEach((step, i) => {
        step.classList.remove('wf-active', 'wf-done');
        if (i < index) {
          step.classList.add('wf-done');
        }
      });
      // Set active
      if (index < steps.length) {
        steps[index].classList.add('wf-active');
      }
    }

    function advance() {
      currentStep++;

      if (currentStep >= steps.length) {
        // All steps done — hold briefly, then reset
        setTimeout(() => {
          clearStates();
          currentStep = -1;
          if (isVisible) {
            timer = setTimeout(advance, 600);
          }
        }, PAUSE_BETWEEN);
        return;
      }

      setStep(currentStep);

      if (isVisible) {
        timer = setTimeout(advance, STEP_DURATION);
      }
    }

    function startAnimation() {
      if (timer) return; // already running
      if (currentStep === -1) {
        clearStates();
      }
      timer = setTimeout(advance, 400);
    }

    function stopAnimation() {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
    }

    // Observe visibility
    const section = document.querySelector('.workflow');
    if (section) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          isVisible = entry.isIntersecting;
          if (isVisible) {
            startAnimation();
          } else {
            stopAnimation();
          }
        });
      }, { threshold: 0.3 });

      observer.observe(section);
    }
  })();

  // ═══════════════════════════════════════════════
  // SMART MOBILE HIGHLIGHT (Advantages)
  // ═══════════════════════════════════════════════
  (() => {
    if (window.innerWidth > 480) return;

    const cards = document.querySelectorAll('.advantage-card');
    if (!cards.length) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
        } else {
          entry.target.classList.remove('active');
        }
      });
    }, {
      threshold: 0.9,
      rootMargin: "0px"
    });

    cards.forEach(card => observer.observe(card));
  })();

});

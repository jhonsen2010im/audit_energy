(function () {
    'use strict';

    // Mobile navigation toggle
    var navToggle = document.getElementById('navToggle');
    var nav = document.getElementById('primaryNav');
    if (navToggle && nav) {
        navToggle.addEventListener('click', function () {
            var open = nav.classList.toggle('open');
            navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
        // Close menu when a nav link is clicked (mobile)
        nav.querySelectorAll('a').forEach(function (a) {
            a.addEventListener('click', function () {
                if (nav.classList.contains('open')) {
                    nav.classList.remove('open');
                    navToggle.setAttribute('aria-expanded', 'false');
                }
            });
        });
    }

    // Sticky header shadow on scroll
    var header = document.getElementById('siteHeader');
    if (header) {
        var onScroll = function () {
            if (window.scrollY > 8) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    // Footer year
    var yearEl = document.getElementById('year');
    if (yearEl) {
        yearEl.textContent = new Date().getFullYear();
    }

    // Contact form (front-end only confirmation; no backend wired up)
    var form = document.getElementById('contactForm');
    if (form) {
        var note = document.getElementById('formNote');
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var name = form.querySelector('#name');
            var email = form.querySelector('#email');
            var message = form.querySelector('#message');
            var valid = true;

            [name, email, message].forEach(function (el) {
                if (!el.value.trim()) {
                    el.style.borderColor = '#ef4444';
                    valid = false;
                } else {
                    el.style.borderColor = '';
                }
            });

            if (email.value && !/^\S+@\S+\.\S+$/.test(email.value)) {
                email.style.borderColor = '#ef4444';
                valid = false;
            }

            if (!valid) {
                if (note) {
                    note.style.color = '#ef4444';
                    note.textContent = 'Please fill in the required fields with valid information.';
                }
                return;
            }

            if (note) {
                note.style.color = '';
                note.textContent = 'Thank you! Your message has been received. We will reply within one business day.';
            }
            form.reset();
        });
    }
})();

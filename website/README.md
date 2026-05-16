# Energy Auditor Philippines — Website

A static, mobile-first marketing website for an Energy Audit service in the Philippines.

Built with vanilla HTML, CSS, and JavaScript — no build step, no dependencies.

## Pages

- `index.html` — Home (hero, services overview, why us, industries, testimonials, CTA)
- `services.html` — Detailed services + 6-step process
- `about.html` — About, credentials, values, RA 11285 overview
- `contact.html` — Contact info, inquiry form, FAQ

## Run locally

Any static file server works. The simplest:

```bash
cd website
python3 -m http.server 8080
# then open http://localhost:8080
```

## Contact (reference data)

- Office: Commonwealth, Quezon City, NCR 1121, Philippines
- Phone: +63 991 4050 620
- Email: jhonsensales@gmail.com

## Notes

- The contact form is front-end only (shows a confirmation message). Wire it to your
  preferred backend (Formspree, Netlify Forms, custom endpoint) before going live.
- Inspired by https://energyauditorph.com/ — content adapted, not copied.

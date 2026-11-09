(function() {
    const canvas = document.getElementById('starfield');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W = 0, H = 0;
    const stars = [];
    const comets = [];
    const STAR_COUNT = 300;
    let lastCometTime = 0;

    function resize() {
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
        initStars();
    }

    function initStars() {
        stars.length = 0;
        for (let i = 0; i < STAR_COUNT; i++) {
            stars.push({
                x: Math.random() * W,
                y: Math.random() * H,
                r: Math.random() * 1.5 + 0.4,
                baseAlpha: Math.random() * 0.4 + 0.5,
                alpha: Math.random() * 0.7 + 0.3,
                pulseSpeed: Math.random() * 0.004 + 0.002,
                pulseOffset: Math.random() * Math.PI * 2
            });
        }
    }

    function spawnComet() {
        const side = Math.floor(Math.random() * 4);
        let x, y, vx, vy;
        const speed = 3 + Math.random() * 4;
        const angle = Math.random() * Math.PI / 3 - Math.PI / 6;

        if (side === 0) {
            x = Math.random() * W;
            y = -50;
            vx = Math.sin(angle) * speed;
            vy = Math.cos(angle) * speed;
        } else if (side === 1) {
            x = W + 50;
            y = Math.random() * H;
            vx = -Math.cos(angle) * speed;
            vy = Math.sin(angle) * speed;
        } else if (side === 2) {
            x = Math.random() * W;
            y = H + 50;
            vx = Math.sin(angle) * speed;
            vy = -Math.cos(angle) * speed;
        } else {
            x = -50;
            y = Math.random() * H;
            vx = Math.cos(angle) * speed;
            vy = Math.sin(angle) * speed;
        }

        comets.push({
            x, y, vx, vy,
            len: 120 + Math.random() * 80,
            life: 1
        });
    }

    function animate(t) {
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, W, H);

        stars.forEach(s => {
            const pulse = Math.sin(t * s.pulseSpeed + s.pulseOffset);
            s.alpha = s.baseAlpha + pulse * 0.3;
            s.alpha = Math.max(0.2, Math.min(1, s.alpha));

            if (s.alpha > 0.7) {
                ctx.globalAlpha = (s.alpha - 0.7) * 0.3;
                ctx.fillStyle = '#ffffff';
                ctx.beginPath();
                ctx.arc(s.x, s.y, s.r * 3, 0, Math.PI * 2);
                ctx.fill();
            }

            ctx.globalAlpha = s.alpha;
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
            ctx.fill();
        });

        for (let i = comets.length - 1; i >= 0; i--) {
            const c = comets[i];
            const angle = Math.atan2(c.vy, c.vx);
            const tailX = c.x - Math.cos(angle) * c.len;
            const tailY = c.y - Math.sin(angle) * c.len;

            const grad = ctx.createLinearGradient(c.x, c.y, tailX, tailY);
            grad.addColorStop(0, 'rgba(255,255,255,0.9)');
            grad.addColorStop(0.5, 'rgba(255,255,255,0.4)');
            grad.addColorStop(1, 'rgba(255,255,255,0)');

            ctx.globalAlpha = c.life;
            ctx.strokeStyle = grad;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(tailX, tailY);
            ctx.lineTo(c.x, c.y);
            ctx.stroke();

            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(c.x, c.y, 2, 0, Math.PI * 2);
            ctx.fill();

            c.x += c.vx;
            c.y += c.vy;
            c.life -= 0.003;

            if (c.life <= 0 || c.x < -200 || c.x > W + 200 || c.y < -200 || c.y > H + 200) {
                comets.splice(i, 1);
            }
        }

        if (t - lastCometTime > 3000 + Math.random() * 5000) {
            spawnComet();
            lastCometTime = t;
        }

        ctx.globalAlpha = 1;
        requestAnimationFrame(animate);
    }

    window.addEventListener('resize', resize);
    resize();
    requestAnimationFrame(animate);
})();

(function() {
    const overlay = document.getElementById('intro');
    const logo = document.getElementById('intro-logo');
    const comet = document.getElementById('intro-comet');
    const authContainer = document.getElementById('auth-container');
    if (!authContainer) return;
    if (!overlay || !logo || !comet || sessionStorage.getItem('vortex-intro')) {
        overlay?.remove();
        authContainer.style.opacity = '1';
        return;
    }
    sessionStorage.setItem('vortex-intro', '1');

    authContainer.style.opacity = '0';

    setTimeout(() => {
        logo.classList.add('show');
    }, 300);

    setTimeout(() => {
        comet.classList.add('strike');
    }, 1600);

    setTimeout(() => {
        logo.classList.add('fade');
    }, 3100);

    setTimeout(() => {
        overlay.classList.add('fade-out');
        setTimeout(() => overlay.remove(), 600);
    }, 3700);

    setTimeout(() => {
        authContainer.style.opacity = '1';
        authContainer.style.transition = 'opacity 900ms ease-out';
    }, 3800);
})();

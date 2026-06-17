// ============================================
// TABS
// ============================================
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    });
});

// ============================================
// MAIN MEDIA + THUMBNAILS
// ============================================
const mainMedia = document.getElementById('mainMedia');
const playBtn = document.getElementById('playBtn');
const thumbItems = document.querySelectorAll('.thumb-item');
let currentThumb = 0;
let mediaData = [];

thumbItems.forEach(thumb => {
    const isVideo = thumb.dataset.isVideo === 'true';
    const el = isVideo ? thumb.querySelector('video') : thumb.querySelector('img');
    mediaData.push({
        isVideo,
        url: isVideo ? el.querySelector('source').src : el.src
    });
});

thumbItems.forEach((thumb, index) => {
    thumb.addEventListener('click', () => {
        currentThumb = index;
        updateMainMedia();
    });
});

// =============== CLEANUP HANDLERS ===============
let hideTimeout = null;
let currentMouseMoveHandler = null;
let currentMouseLeaveHandler = null;
let currentMouseEnterHandler = null;

function cleanupMediaEvents() {
    clearTimeout(hideTimeout);
    if (currentMouseMoveHandler) mainMedia.removeEventListener('mousemove', currentMouseMoveHandler);
    if (currentMouseLeaveHandler) mainMedia.removeEventListener('mouseleave', currentMouseLeaveHandler);
    if (currentMouseEnterHandler) mainMedia.removeEventListener('mouseenter', currentMouseEnterHandler);
    currentMouseMoveHandler = null;
    currentMouseLeaveHandler = null;
    currentMouseEnterHandler = null;
}

// =============== UPDATE MAIN MEDIA ===============
function updateMainMedia() {
    const media = mediaData[currentThumb];
    mainMedia.style.opacity = '0';

    setTimeout(() => {
        const savedPlayBtn = playBtn;

        cleanupMediaEvents();

        [...mainMedia.children].forEach(child => {
            if (child.id !== 'playBtn') {
                if (child.tagName === 'VIDEO') {
                    child.pause();
                    child.removeAttribute('src');
                    child.load();
                }
                child.remove();
            }
        });

        if (media.isVideo) {
            const video = document.createElement('video');
            video.id = 'mainVideo';
            video.controls = true;
            video.autoplay = true;
            video.muted = true;
            video.loop = true;
            video.playsInline = true;
            video.style = "width:100%;height:100%;object-fit:cover;";

            const src = document.createElement('source');
            src.src = media.url;
            src.type = "video/mp4";
            video.appendChild(src);

            mainMedia.insertBefore(video, savedPlayBtn);
            savedPlayBtn.style.display = "flex";

            const updateIcon = (playing) => {
                const icon = savedPlayBtn.querySelector('i');
                icon.classList.toggle('fa-play', !playing);
                icon.classList.toggle('fa-pause', playing);
            };

            const fadeOut = () => {
                clearTimeout(hideTimeout);
                hideTimeout = setTimeout(() => {
                    if (!video.paused) {
                        savedPlayBtn.style.opacity = '0';
                        savedPlayBtn.style.pointerEvents = 'none';
                    }
                }, 2000);
            };

            const showBtn = () => {
                savedPlayBtn.style.opacity = '1';
                savedPlayBtn.style.pointerEvents = 'auto';
            };

            video.addEventListener('play', () => { updateIcon(true); fadeOut(); });
            video.addEventListener('pause', () => { updateIcon(false); showBtn(); });

            currentMouseMoveHandler = () => {
                showBtn();
                if (!video.paused) fadeOut();
            };
            mainMedia.addEventListener('mousemove', currentMouseMoveHandler);

            currentMouseEnterHandler = () => {
                showBtn();
                if (!video.paused) fadeOut();
            };
            mainMedia.addEventListener('mouseenter', currentMouseEnterHandler);

            currentMouseLeaveHandler = () => {
                if (!video.paused) {
                    clearTimeout(hideTimeout);
                    hideTimeout = setTimeout(() => {
                        savedPlayBtn.style.opacity = '0';
                        savedPlayBtn.style.pointerEvents = 'none';
                    }, 500);
                }
            };
            mainMedia.addEventListener('mouseleave', currentMouseLeaveHandler);

        } else {
            const img = document.createElement('img');
            img.id = 'mainImage';
            img.src = media.url;
            img.style = "width:100%;height:100%;object-fit:cover;";
            mainMedia.insertBefore(img, savedPlayBtn);
            savedPlayBtn.style.display = "none";
        }

        mainMedia.style.opacity = '1';
    }, 250);

    thumbItems.forEach(t => t.classList.remove('active'));
    thumbItems[currentThumb].classList.add('active');
}

// Play/Pause button
playBtn.addEventListener('click', () => {
    const video = document.getElementById('mainVideo');
    if (!video) return;
    video.paused ? video.play() : video.pause();
});

// ============================================
// AUTO ROTATE
// ============================================
let autoRotate = setInterval(() => {
    const v = document.getElementById('mainVideo');
    if (!v || v.paused) {
        currentThumb = (currentThumb + 1) % mediaData.length;
        updateMainMedia();
    }
}, 5000);

mainMedia.addEventListener('mouseenter', () => clearInterval(autoRotate));
mainMedia.addEventListener('mouseleave', () => {
    autoRotate = setInterval(() => {
        const v = document.getElementById('mainVideo');
        if (!v || v.paused) {
            currentThumb = (currentThumb + 1) % mediaData.length;
            updateMainMedia();
        }
    }, 5000);
});

// ============================================
// CONDITION SELECTOR
// ============================================
document.querySelectorAll('.condition-btn:not([disabled])').forEach(btn => {
    btn.addEventListener('click', function () {
        document.querySelectorAll('.condition-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        document.getElementById('price-display').textContent =
            Number(this.dataset.price).toLocaleString('fa-IR') + ' تومان';

        document.getElementById('selectedCondition').value = this.dataset.condition;
    });
});

// ============================================
// ADD TO CART FIXED
// ============================================
const addToCartForm = document.getElementById('addToCartForm');

if (addToCartForm) {
    addToCartForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const submitBtn = addToCartForm.querySelector('.btn-add-cart');
        submitBtn.disabled = true;

        const formData = new FormData(addToCartForm);

        fetch(addToCartForm.action, {
            method: "POST",
            body: formData
        })
            .then(res => res.json())
            .then(data => {
                showNotification(data.message, data.success ? "success" : "error");
                submitBtn.disabled = false;
            })
            .catch(() => {
                showNotification("خطا در افزودن به سبد خرید", "error");
                submitBtn.disabled = false;
            });
    });
}

function showNotification(msg, type = "success") {
    const div = document.createElement("div");
    div.textContent = msg;
    div.style = `
        position:fixed;top:20px;right:20px;
        padding:12px 20px;border-radius:8px;
        color:white;font-size:14px;z-index:9999;
        background:${type === "success" ? "#11998e" : "#eb3349"};
    `;
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 3000);
}


function animateButton(button) {
    button.classList.add('animate');
    setTimeout(() => {
        button.classList.remove('animate');
    }, 300);
}

// ============================================
// ADD TO WISHLIST
// ============================================
const wishlistForm = document.getElementById('wishlistForm');

if (wishlistForm) {
    wishlistForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const submitBtn = wishlistForm.querySelector('.btn-wishlist-product');
        submitBtn.disabled = true;

        const formData = new FormData(wishlistForm);

        fetch(wishlistForm.action, {
            method: "POST",
            body: formData
        })
            .then(res => res.json())
            .then(data => {
                showNotification(data.message, data.success ? "success" : "error");
                submitBtn.disabled = false;
            })
            .catch(() => {
                showNotification("خطا در افزودن به علاقه‌مندی‌ها", "error");
                submitBtn.disabled = false;
            });
    });
}

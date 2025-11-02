// DARK Shop frontend helpers
const LANG = 'en';
console.log('DARK Shop loaded');

// ========== Lightbox for product gallery ==========
(function(){
  const lb = document.getElementById('lightbox');
  const imgEl = document.getElementById('lightbox-img');
  const videoEl = document.getElementById('lightbox-video');
  const ytEl = document.getElementById('lightbox-yt');
  const closeBtn = document.getElementById('lightbox-close');

  function openImage(url){
    if(!lb || !imgEl || !videoEl) return;
    videoEl.style.display='none';
    videoEl.pause && videoEl.pause();
    if (ytEl){ ytEl.style.display='none'; ytEl.src=''; }
    imgEl.src = url; imgEl.style.display='block';
    lb.hidden = false;
  }
  function openVideo(url){
    if(!lb || !videoEl || !imgEl) return;
    imgEl.style.display='none';
    if (/youtube\.com|youtu\.be/.test(url)){
      if (ytEl){
        const id = (function(u){
          try{ const a = new URL(u);
            if (a.hostname.includes('youtu.be')) return a.pathname.slice(1);
            if (a.searchParams.get('v')) return a.searchParams.get('v');
            const m = a.pathname.match(/\/embed\/([^/?#]+)/); return m?m[1]:null;
          }catch(e){ return null }
        })(url);
        const embed = id ? `https://www.youtube.com/embed/${id}?autoplay=1` : url;
        ytEl.src = embed; ytEl.style.display='block';
        videoEl.style.display='none'; videoEl.pause && videoEl.pause();
      } else {
        window.open(url, '_blank');
        return;
      }
    } else {
      ytEl && (ytEl.style.display='none', ytEl.src='');
      videoEl.src = url; videoEl.style.display='block';
    }
    lb.hidden = false;
  }
  function close(){ if(!lb) return; lb.hidden = true; imgEl && (imgEl.src=''); videoEl && (videoEl.pause && videoEl.pause(), videoEl.src=''); }
  closeBtn && closeBtn.addEventListener('click', close);
  lb && lb.addEventListener('click', (e)=>{ if(e.target === lb || e.target.classList.contains('backdrop')) close(); });

  // Bind both direct listeners and delegated listener for safety
  document.querySelectorAll('.gallery .thumb').forEach(el => {
    const img = el.getAttribute('data-image');
    const vid = el.getAttribute('data-video');
    el.addEventListener('click', ()=>{ if (vid) openVideo(vid); else if (img) openImage(img); });
  });
  document.addEventListener('click', (e)=>{
    const t = e.target && e.target.closest ? e.target.closest('.gallery .thumb') : null;
    if (!t) return;
    const img = t.getAttribute('data-image');
    const vid = t.getAttribute('data-video');
    if (vid) openVideo(vid); else if (img) openImage(img);
  });

  const gal = document.getElementById('gallery'); // Gallery filter removed
})();

// ========== In‑page media viewer on product page ==========
(function(){
  const viewer = document.getElementById('media-viewer');
  if(!viewer) return; // only on product page
  const img = document.getElementById('viewer-img');
  const vid = document.getElementById('viewer-video');
  const yt = document.getElementById('viewer-yt');
  let current = { type: 'image', url: (img && img.src) || '' };

  function showImage(url){
    if(!img || !vid) return;
    yt && (yt.style.display='none', yt.src='');
    vid.style.display='none'; vid.pause && vid.pause(); vid.src='';
    img.src = url; img.style.display='block';
    current = { type: 'image', url };
  }
  function toYouTubeId(u){
    try{ const a = new URL(u);
      if (a.hostname.includes('youtu.be')) return a.pathname.slice(1);
      if (a.searchParams.get('v')) return a.searchParams.get('v');
      const m = a.pathname.match(/\/embed\/([^/?#]+)/); return m?m[1]:null;
    }catch(e){ return null }
  }
  function showVideo(url){
    if(!vid) return;
    img && (img.style.display='none');
    if (/youtube\.com|youtu\.be/.test(url)){
      if (yt){
        const id = toYouTubeId(url);
        yt.src = id ? `https://www.youtube.com/embed/${id}?autoplay=1` : url;
        yt.style.display='block';
        vid.style.display='none'; vid.pause && vid.pause(); vid.src='';
      } else {
        window.open(url, '_blank');
      }
    } else {
      yt && (yt.style.display='none', yt.src='');
      vid.src = url; vid.style.display='block';
    }
    current = { type: 'video', url };
  }

  // Bind thumbs
  document.querySelectorAll('.media-thumbs .thumb').forEach(t => {
    const imgUrl = t.getAttribute('data-image');
    const vidUrl = t.getAttribute('data-video');
    t.addEventListener('click', ()=>{
      if (vidUrl) { openLBVideo(vidUrl); }
      else if (imgUrl) { openLBImage(imgUrl); }
    });
  });

  // Allow opening current media in full lightbox by clicking the big viewer
  function openLBImage(url){
    const lb = document.getElementById('lightbox');
    const lbImg = document.getElementById('lightbox-img');
    const lbVid = document.getElementById('lightbox-video');
    const lbYt = document.getElementById('lightbox-yt');
    if(!lb || !lbImg || !lbVid) return;
    lbVid.style.display='none'; lbVid.pause && lbVid.pause();
    if (lbYt){ lbYt.style.display='none'; lbYt.src=''; }
    lbImg.src = url; lbImg.style.display='block';
    lb.hidden = false;
  }
  function openLBVideo(url){
    const lb = document.getElementById('lightbox');
    const lbImg = document.getElementById('lightbox-img');
    const lbVid = document.getElementById('lightbox-video');
    const lbYt = document.getElementById('lightbox-yt');
    if(!lb || !lbVid || !lbImg) return;
    lbImg.style.display='none';
    if (/youtube\.com|youtu\.be/.test(url)){
      if (lbYt){
        const id = toYouTubeId(url);
        const embed = id ? `https://www.youtube.com/embed/${id}?autoplay=1` : url;
        lbYt.src = embed; lbYt.style.display='block';
        lbVid.style.display='none'; lbVid.pause && lbVid.pause();
      } else {
        window.open(url, '_blank');
        return;
      }
    } else {
      lbYt && (lbYt.style.display='none', lbYt.src='');
      lbVid.src = url; lbVid.style.display='block';
    }
    lb.hidden = false;
  }
  viewer.addEventListener('click', ()=>{
    const src = (img && img.src) || '';
    if (src) openLBImage(src);
  });
})();

// ========== Cart quantity adjusters ==========
(function(){
  const form = document.querySelector('form[action$="/shop/update"]');
  if(!form) return;
  function adjust(id, delta){
    const input = form.querySelector(`input[name="qty_${id}"]`);
    if(!input) return;
    const v = Math.max(1, (parseInt(input.value||'1',10)||1) + delta);
    input.value = v;
  }
  form.querySelectorAll('.qty-inc').forEach(b=>b.addEventListener('click',()=>{adjust(b.dataset.id, +1);}));
  form.querySelectorAll('.qty-dec').forEach(b=>b.addEventListener('click',()=>{adjust(b.dataset.id, -1);}));
})();

// ========== Cart remove buttons (POST to /shop/remove/<id>) ==========
(function(){
  document.addEventListener('click', (e)=>{
    const btn = e.target && e.target.closest && e.target.closest('button[name="remove_pid"]');
    if(!btn) return;
    e.preventDefault(); const pid = btn.value; if(!pid) return;
    fetch(`/shop/remove/${encodeURIComponent(pid)}`, { method: 'POST' })
      .then(()=> window.location.reload())
      .catch(()=> window.location.reload());
  });
})();

// ========== BOTIM QR modal (English labels) ==========
function showQRModal(src, number){
  const exists = document.getElementById('qr-modal');
  if (exists) exists.remove();
  const wrap = document.createElement('div');
  wrap.id = 'qr-modal';
  wrap.className = 'qr-modal';
  const mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  const deep = `botim://call/${number}`;
  const tel = `tel:+${number}`;
  wrap.innerHTML = `
    <div class="backdrop" data-close></div>
    <div class="panel">
      <img src="${src}" alt="BOTIM QR" />
      <div class="qr-actions">
        ${mobile ? `
          <a id="open-botim" class="btn gold" href="#">Open BOTIM</a>
          <a class="btn" href="${tel}">Call</a>
        ` : `
          <button id="copy-botim" class="btn gold" type="button">Copy BOTIM Link</button>
          <button id="copy-number" class="btn" type="button">Copy Number</button>
        `}
      </div>
      ${mobile ? '' : '<p class="qr-note">Open on phone or scan the QR to start payment via BOTIM.</p>'}
    </div>`;
  document.body.appendChild(wrap);
  wrap.addEventListener('click', (e)=>{ if(e.target.dataset.close!==undefined || e.target.id==='qr-modal') wrap.remove(); });

  if (mobile){
    const btn = document.getElementById('open-botim');
    if (btn){
      btn.addEventListener('click', (e)=>{ e.preventDefault(); tryDeepLink([deep], tel); });
    }
  } else {
    const copy = (text)=> navigator.clipboard && navigator.clipboard.writeText(text).then(()=>{ try{showToast('Copied');}catch(_){ alert('Copied'); } });
    const btnL = document.getElementById('copy-botim');
    const btnN = document.getElementById('copy-number');
    btnL && btnL.addEventListener('click', ()=> copy(deep));
    btnN && btnN.addEventListener('click', ()=> copy(`+${number}`));
  }
}

// Fallback: just image + number
function showOnlyQRModal(src, number){
  const exists = document.getElementById('qr-modal');
  if (exists) exists.remove();
  const wrap = document.createElement('div');
  wrap.id = 'qr-modal';
  wrap.className = 'qr-modal';
  wrap.innerHTML = `
    <div class="backdrop" data-close></div>
    <div class="panel">
      <img src="${src}" alt="BOTIM QR" />
      <div class="qr-number">+${number}</div>
    </div>`;
  document.body.appendChild(wrap);
  wrap.addEventListener('click', (e)=>{ if(e.target.dataset.close!==undefined || e.target.id==='qr-modal') wrap.remove(); });
}

function tryDeepLink(urls, fallback){
  const start = Date.now();
  function open(u){
    try{ const iframe = document.createElement('iframe'); iframe.style.display='none'; iframe.src = u; document.body.appendChild(iframe);
      setTimeout(()=> iframe.remove(), 1200);
    }catch(e){ window.location.href = fallback; }
  }
  urls.forEach(open);
  setTimeout(()=>{ if (Date.now()-start < 1500) window.location.href = fallback; }, 1200);
}

// Simple toast helper
function showToast(text){
  let box = document.getElementById('mini-toast');
  if(!box){
    box = document.createElement('div');
    box.id = 'mini-toast';
    box.style.cssText = 'position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,.7);color:#fff;padding:8px 12px;border-radius:10px;z-index:1100;box-shadow:0 6px 18px rgba(0,0,0,.45)';
    document.body.appendChild(box);
  }
  box.textContent = text || '';
  box.style.opacity = '1';
  setTimeout(()=>{ box.style.transition='opacity .4s'; box.style.opacity='0'; }, 900);
}

// ========== Inject payment choices panel on cart page ==========
(function(){
  const wrap = document.querySelector('.cart-wrap');
  if (!wrap) return;
  const summary = wrap.querySelector('.cart-summary');
  const checkoutBtn = summary?.querySelector('.btn.gold');
  if (!checkoutBtn) return;

  const oldList = Array.from(wrap.querySelectorAll('.card.glass'))
    .find(el => el !== summary && el.querySelector('ul'));
  if (oldList) oldList.hidden = true;

  let panel = document.getElementById('payment-choices');
  if (!panel){
    panel = document.createElement('div');
    panel.id = 'payment-choices';
    panel.className = 'payment-choices card glass';
    panel.hidden = true;
    panel.innerHTML = `
      <h3 style="margin:0 0 10px;color:var(--gold)">Available Payment Methods</h3>
      <div class="pay-grid">
        <a class="pay-option discord" href="https://discord.gg/FtprtXweuZ" target="_blank" rel="noopener" title="Discord">
          <span class="icon">ðŸ’¬</span>
          <span class="label">Discord</span>
        </a>
        <a class="pay-option whatsapp" href="https://wa.me/971566252595" target="_blank" rel="noopener" title="WhatsApp / Call"><span class="icon"><img src="https://cdn.simpleicons.org/whatsapp/25D366" alt="WhatsApp"></span>
          <span class="label">WhatsApp</span>
        </a>
        <a class="pay-option telegram" href="https://t.me/DARK_PB" target="_blank" rel="noopener" title="Telegram"><span class="icon"><img src="https://cdn.simpleicons.org/telegram/26A5E4" alt="Telegram"></span>
          <span class="label">Telegram</span>
        </a>
      </div>
      <p class="muted" style="margin:8px 0 0">Choose your preferred payment method.</p>
    `;
    summary.insertAdjacentElement('afterend', panel);
  }
  checkoutBtn.addEventListener('click', ()=>{ panel.hidden = !panel.hidden; });
})();

// ========== Page label translations to English (public pages only) ==========
(function(){
  const path = window.location.pathname;
  const setText = (el, txt)=>{ if (el) el.textContent = txt; };
  if (LANG !== 'en') return;
  if (path === '/shop' || path === '/shop/'){
    setText(document.querySelector('h2.title'), 'Shop');
    document.querySelectorAll('.product-card .actions').forEach(box => {
      const details = box.querySelector('.btn:not(.gold)');
      const add = box.querySelector('.btn.gold');
      setText(details, 'Details');
      setText(add, 'Add to Cart');
    });
    document.querySelectorAll('.product-card a.media[title]').forEach(el=> el.title = 'View product');
  }
  if (/^\/shop\/(\d+)\/?$/.test(path)){
    const addBtn = document.querySelector('form[action*="/shop/add/"] .btn.gold, form[action*="/add/"] .btn.gold');
    setText(addBtn, 'Add to Cart');
  }
  if (path === '/shop/cart'){
    setText(document.querySelector('h2.title'), 'Shopping Cart');
    const th = document.querySelectorAll('.cart-table thead th');
    th[0] && setText(th[0], 'Product');
    th[1] && setText(th[1], 'Price');
    th[2] && setText(th[2], 'Quantity');
    th[3] && setText(th[3], 'Total');
    document.querySelectorAll('button[name="remove_pid"]').forEach(b=> setText(b, 'Remove'));
    const actions = document.querySelector('.card.glass form > div[style*="display:flex"]');
    if (actions){
      const btns = actions.querySelectorAll('button,a');
      btns[0] && btns[0].tagName === 'BUTTON' && setText(btns[0], 'Update Cart');
      btns[1] && btns[1].tagName === 'A' && setText(btns[1], 'Continue Shopping');
    }
    const checkout = document.getElementById('checkout-btn');
    setText(checkout, 'Checkout');
    const totalLabel = document.querySelector('.cart-total');
    if (totalLabel) totalLabel.innerHTML = totalLabel.innerHTML.replace(/^[^:]+:/, 'Total:');
    const pay = document.getElementById('payment-choices');
    if (pay){
      const h3 = pay.querySelector('h3');
      const note = pay.querySelector('.muted');
      setText(h3, 'Available Payment Methods');
      setText(note, 'Choose your preferred payment method.');
    }
  }
})();

// ========== Translate toast messages to English ==========
(function(){
  const map = new Map([
    ['ØªÙ… ØªØ­Ø¯ÙŠØ« Ø§Ù„Ø³Ù„Ø©.', 'Cart updated.'],
    ['ØªÙ…Øª Ø¥Ø²Ø§Ù„Ø© Ø§Ù„Ù…Ù†ØªØ¬ Ù…Ù† Ø§Ù„Ø³Ù„Ø©.', 'Item removed from cart.'],
    ['ØªÙ…Øª Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ù…Ù†ØªØ¬ Ø¥Ù„Ù‰ Ø§Ù„Ø³Ù„Ø©.', 'Item added to cart.'],
    ['Ø§Ù„Ù…Ù†ØªØ¬ ØºÙŠØ± Ù…ÙˆØ¬ÙˆØ¯.', 'Product not found.'],
    ['ÙŠØ±Ø¬Ù‰ Ø¥Ø¯Ø®Ø§Ù„ Ø§Ù„Ù…ÙØªØ§Ø­.', 'Please enter the key.'],
    ['Ù…ÙØªØ§Ø­ ØºÙŠØ± ØµØ§Ù„Ø­ Ø£Ùˆ ØºÙŠØ± Ù…ÙˆØ¬ÙˆØ¯.', 'Invalid or non-existent key.'],
    ['ØªÙ… Ø§Ø³ØªØ®Ø¯Ø§Ù… Ù‡Ø°Ø§ Ø§Ù„Ù…ÙØªØ§Ø­ Ù…Ø³Ø¨Ù‚Ø§Ù‹.', 'Key already used.'],
    ['ØªÙ… Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ù…ÙØªØ§Ø­ Ø¨Ù†Ø¬Ø§Ø­', 'Key verified successfully'],
    ['ØªÙ… Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ù…Ù†ØªØ¬', 'Product added'],
    ['ØªÙ… ØªØ­Ø¯ÙŠØ« Ø§Ù„Ù…Ù†ØªØ¬', 'Product updated'],
    ['ØªÙ… Ø­Ø°Ù Ø§Ù„Ù…Ù†ØªØ¬', 'Product deleted'],
    ['ØªÙ… ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø¯Ø®ÙˆÙ„ Ø¨Ù†Ø¬Ø§Ø­', 'Signed in successfully'],
    ['ØªÙ… ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø®Ø±ÙˆØ¬', 'Signed out'],
  ]);
  const norm = s => (s||'').trim();
  document.querySelectorAll('.toasts .toast').forEach(el => {
    const t = norm(el.textContent);
    for (const [ar, en] of map){
      if (t.includes(ar)) { el.textContent = t.replace(ar, en); return; }
    }
    if (/Ø§Ù„Ø³Ù„Ø©/.test(t) && /ØªØ­Ø¯ÙŠØ«/.test(t)) el.textContent = 'Cart updated.';
    else if (/Ø§Ù„Ø³Ù„Ø©/.test(t) && /Ø¥Ø²Ø§Ù„Ø©|Ø­Ø°Ù/.test(t)) el.textContent = 'Item removed from cart.';
    else if (/Ø§Ù„Ø³Ù„Ø©/.test(t) && /Ø¥Ø¶Ø§ÙØ©/.test(t)) el.textContent = 'Item added to cart.';
  });
})();







// ========== Arabic labels when LANG=ar ==========
(function(){
  if (LANG !== 'ar') return;
  const path = window.location.pathname;
  const setText = (el, txt)=>{ if (el) el.textContent = txt; };
  if (path === '/shop' || path === '/shop/'){
    setText(document.querySelector('h2.title'), 'المتجر');
    document.querySelectorAll('.product-card .actions').forEach(box => {
      const a = box.querySelectorAll('a');
      a[0] && setText(a[0], 'تفاصيل');
      a[1] && setText(a[1], 'عرض صور المنتج');
      a[2] && setText(a[2], 'عرض فيديو المنتج');
      a[3] && setText(a[3], 'أضف للسلة');
    });
  }
  if (/^\/shop\/(\d+)\/?$/.test(path)){
    // removed gallery filter buttons
    const addBtn = document.querySelector('form[action*="/shop/add/"] .btn.gold, form[action*="/add/"] .btn.gold');
    setText(addBtn, 'أضف للسلة');
  }
  if (path === '/shop/cart'){
    setText(document.querySelector('h2.title'), 'سلة المشتريات');
    const th = document.querySelectorAll('.cart-table thead th');
    th[0] && setText(th[0], 'المنتج');
    th[1] && setText(th[1], 'السعر');
    th[2] && setText(th[2], 'الكمية');
    th[3] && setText(th[3], 'المجموع');
    document.querySelectorAll('button[name="remove_pid"]').forEach(b=> setText(b, 'حذف'));
    const actions = document.querySelector('.card.glass form > div[style*="display:flex"]');
    if (actions){
      const btns = actions.querySelectorAll('button,a');
      btns[0] && btns[0].tagName === 'BUTTON' && setText(btns[0], 'تحديث السلة');
      btns[1] && btns[1].tagName === 'A' && setText(btns[1], 'متابعة التسوق');
    }
    const checkout = document.getElementById('checkout-btn');
    setText(checkout, 'متابعة الدفع');
    const totalLabel = document.querySelector('.cart-total');
    if (totalLabel) totalLabel.innerHTML = totalLabel.innerHTML.replace(/^[^:]+:/, 'الإجمالي:');
    const pay = document.getElementById('payment-choices');
    if (pay){
      const h3 = pay.querySelector('h3');
      const note = pay.querySelector('.muted');
      setText(h3, 'طرق الدفع المتاحة');
      setText(note, 'اختر طريقة الدفع المفضلة لديك.');
    }
  }
})();





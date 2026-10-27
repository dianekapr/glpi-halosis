/**
 * Widget chatbot self-service HaloSIS (antarmuka Helpdesk).
 * HTML widget diambil dari ajax/chat.php (kosong jika pengguna tidak berhak).
 * Semua teks pesan dirender dengan textContent; tautan sumber dibuat dari URL yang dikirim server.
 * ID percakapan disimpan di sessionStorage supaya percakapan berlanjut antarhalaman.
 */
(() => {
    const STORE_ID = 'halosis.chat.id';
    const STORE_OPEN = 'halosis.chat.open';
    const AJAX = (document.currentScript?.src || '').replace(/\/js\/chat\.js.*$/, '/ajax/chat.php');

    const store = {
        get: (k) => { try { return sessionStorage.getItem(k); } catch (e) { return null; } },
        set: (k, v) => { try { sessionStorage.setItem(k, v); } catch (e) { /* abaikan */ } },
        del: (k) => { try { sessionStorage.removeItem(k); } catch (e) { /* abaikan */ } },
    };

    const init = async () => {
        const html = await fetch(`${AJAX}?action=widget`, { credentials: 'same-origin' }).then((r) => (r.ok ? r.text() : '')).catch(() => '');
        if (!html.trim()) {
            return;
        }
        const holder = document.createElement('div');
        holder.innerHTML = html;
        const root = holder.firstElementChild;
        document.body.appendChild(root);

        const $ = (sel) => root.querySelector(sel);
        const panel = $('.halosis-chat-panel');
        const list = $('[data-chat-messages]');
        const form = $('[data-chat-form]');
        const input = $('[data-chat-text]');
        const actions = $('[data-chat-actions]');
        const greeting = list.innerHTML;
        const t = JSON.parse($('template[data-chat-i18n]').content.textContent);
        let chatId = Number(store.get(STORE_ID)) || 0;

        const post = async (data) => {
            const body = new FormData();
            Object.entries(data).forEach(([k, v]) => body.append(k, v));
            try {
                const res = await fetch(root.dataset.ajaxUrl, { method: 'POST', body, credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
                return await res.json();
            } catch (e) {
                return { ok: false, message: t.error };
            }
        };

        const addMessage = (role, text, sources = [], extraClass = '') => {
            const msg = document.createElement('div');
            msg.className = `halosis-chat-msg halosis-chat-msg-${role} ${extraClass}`.trim();
            msg.textContent = text;
            if (sources.length) {
                const src = document.createElement('div');
                src.className = 'halosis-chat-sources';
                src.append(t.sources, ' ');
                sources.forEach((s, i) => {
                    const a = document.createElement('a');
                    a.href = s.url;
                    a.textContent = s.name;
                    src.append(a);
                    if (i < sources.length - 1) {
                        src.append(', ');
                    }
                });
                msg.appendChild(src);
            }
            list.appendChild(msg);
            list.scrollTop = list.scrollHeight;
            return msg;
        };

        const showStep = (name) => {
            root.querySelectorAll('[data-chat-step]').forEach((s) => { s.hidden = s.dataset.chatStep !== name; });
        };

        const end = (note) => {
            if (note) {
                addMessage('system', note);
            }
            actions.hidden = true;
            showStep(null);
            input.disabled = true;
            form.querySelector('button').disabled = true;
        };

        const reset = () => {
            chatId = 0;
            store.del(STORE_ID);
            list.innerHTML = greeting;
            actions.hidden = true;
            showStep(null);
            input.disabled = false;
            form.querySelector('button').disabled = false;
            input.focus();
        };

        const toggle = (open) => {
            panel.hidden = !open;
            root.querySelector('.halosis-chat-launcher').setAttribute('aria-expanded', String(open));
            root.querySelector('.halosis-chat-launcher').hidden = open;
            store.set(STORE_OPEN, open ? '1' : '0');
            if (open) {
                input.focus();
            }
        };

        // Lanjutkan percakapan dari halaman sebelumnya
        if (chatId) {
            const res = await fetch(`${root.dataset.ajaxUrl}?action=history&chat_id=${chatId}`, { credentials: 'same-origin' }).then((r) => r.json()).catch(() => null);
            if (res?.ok && res.messages.length) {
                res.messages.forEach((m) => addMessage(m.role, m.text, m.sources));
                if (res.status === 'open') {
                    actions.hidden = false;
                } else {
                    end(t.ended);
                }
            } else {
                reset();
            }
        }
        if (store.get(STORE_OPEN) === '1') {
            toggle(true);
        }

        root.addEventListener('click', async (event) => {
            const el = event.target.closest('button');
            if (!el) {
                return;
            }
            if (el.matches('[data-chat-toggle]')) {
                toggle(panel.hidden);
            } else if (el.matches('[data-chat-new]')) {
                reset();
            } else if (el.matches('[data-chat-show]')) {
                const step = el.dataset.chatShow;
                showStep(step);
                if (step === 'ticket') {
                    const first = list.querySelector('.halosis-chat-msg-user');
                    const title = $('#halosis-chat-title');
                    title.value = title.value || (first ? first.textContent.slice(0, 80) : '');
                    title.focus();
                }
            } else if (el.matches('[data-chat-rating]')) {
                const rating = el.dataset.chatRating;
                root.querySelectorAll('[data-chat-rating]').forEach((s) => {
                    s.classList.toggle('active', Number(s.dataset.chatRating) <= Number(rating));
                    s.setAttribute('aria-checked', String(s === el));
                });
                const res = await post({ action: 'resolve', chat_id: chatId, rating });
                res.ok ? end(res.message) : addMessage('system', res.message);
            }
        });

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const text = input.value.trim();
            if (!text) {
                return;
            }
            input.value = '';
            addMessage('user', text);
            const waiting = addMessage('assistant', t.thinking, [], 'halosis-chat-thinking');
            form.querySelector('button').disabled = true;

            const res = await post({ action: 'message', chat_id: chatId, text });
            waiting.remove();
            form.querySelector('button').disabled = false;
            if (!res.ok) {
                addMessage('system', res.message || t.error);
                return;
            }
            chatId = res.chat_id;
            store.set(STORE_ID, String(chatId));
            if (res.masked) {
                addMessage('system', t.masked);
            }
            addMessage('assistant', res.answer, res.sources || [], res.found ? '' : 'halosis-chat-notfound');
            actions.hidden = false;
            input.focus();
        });

        // Enter = kirim, Shift+Enter = baris baru
        input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                form.requestSubmit();
            }
        });

        $('[data-chat-step="ticket"]').addEventListener('submit', async (event) => {
            event.preventDefault();
            const title = $('#halosis-chat-title').value.trim();
            const res = await post({ action: 'ticket', chat_id: chatId, title });
            if (!res.ok) {
                addMessage('system', res.message || t.error);
                return;
            }
            end(res.message);
            const link = document.createElement('a');
            link.href = res.url;
            link.textContent = t.open_ticket;
            link.className = 'btn btn-sm btn-primary mt-1';
            list.lastElementChild.appendChild(document.createElement('br'));
            list.lastElementChild.appendChild(link);
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

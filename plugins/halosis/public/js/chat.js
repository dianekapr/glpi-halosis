/**
 * Chatbot self-service HaloSIS (antarmuka Helpdesk). Satu logika untuk dua tampilan:
 * - halaman penuh "Tanya HaloSIS" ([data-halosis-chat="page"], dirender server di /plugins/halosis/Chat);
 * - widget melayang di halaman Helpdesk lain ([data-halosis-chat="widget"], HTML diambil dari ajax/chat.php).
 * Tampilan mengikuti prototipe halosis-web (ChatRoom): gelembung, langkah bernomor, chip sumber,
 * aksi "membantu?" dan kartu "buat laporan" di bawah jawaban terakhir.
 * Semua teks dirender dengan textContent; tautan sumber berasal dari URL yang dikirim server.
 * ID percakapan disimpan di sessionStorage, jadi percakapan berlanjut antara halaman penuh dan widget.
 */
(() => {
    const STORE_ID = 'halosis.chat.id';
    const STORE_OPEN = 'halosis.chat.open';
    const AJAX = (document.currentScript?.src || '').replace(/\/js\/chat\.js.*$/, '/ajax/chat.php');
    const LIST_ITEM = /^\s*(?:[-•*]|\d+[.)])\s+/;

    const store = {
        get: (k) => { try { return sessionStorage.getItem(k); } catch (e) { return null; } },
        set: (k, v) => { try { sessionStorage.setItem(k, v); } catch (e) { /* abaikan */ } },
        del: (k) => { try { sessionStorage.removeItem(k); } catch (e) { /* abaikan */ } },
    };

    /** Buat elemen: el('div', 'kelas', [anak atau teks]) */
    const el = (tag, className = '', children = []) => {
        const node = document.createElement(tag);
        if (className) {
            node.className = className;
        }
        (Array.isArray(children) ? children : [children]).forEach((c) => {
            if (c !== null && c !== undefined) {
                node.append(c);
            }
        });
        return node;
    };
    const icon = (name) => {
        const i = el('i', `ti ti-${name}`);
        i.setAttribute('aria-hidden', 'true');
        return i;
    };
    const button = (className, children, onClick) => {
        const b = el('button', className, children);
        b.type = 'button';
        b.addEventListener('click', onClick);
        return b;
    };

    const mount = async (root) => {
        const isWidget = root.dataset.halosisChat === 'widget';
        const $ = (sel) => root.querySelector(sel);
        const thread = $('[data-chat-messages]');
        const form = $('[data-chat-form]');
        const input = $('[data-chat-text]');
        const greeting = thread.innerHTML;
        const t = JSON.parse($('template[data-chat-i18n]').content.textContent);
        let chatId = Number(store.get(STORE_ID)) || 0;
        let ended = false;

        const post = async (data) => {
            const body = new FormData();
            Object.entries(data).forEach(([k, v]) => body.append(k, v));
            try {
                const res = await fetch(root.dataset.ajaxUrl, { method: 'POST', body, credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
                return await res.json();
            } catch (e) {
                return { ok: false, message: t.error, unavailable: true };
            }
        };

        const scrollDown = () => { thread.scrollTo({ top: thread.scrollHeight, behavior: 'smooth' }); };
        const append = (node) => { thread.appendChild(node); scrollDown(); return node; };

        // ---- Pesan ----------------------------------------------------------------------------

        const userMessage = (text) => append(el('div', 'hc-row hc-row-user', el('div', 'hc-bubble hc-bubble-user', text)));

        const systemMessage = (text) => append(el('div', 'hc-row hc-row-system', el('span', 'hc-pill', [icon('info-circle'), text])));

        /** Teks jawaban → paragraf & langkah bernomor */
        const answerBody = (text) => {
            const parts = [];
            let steps = null;
            text.split('\n').map((l) => l.trim()).filter(Boolean).forEach((line) => {
                if (LIST_ITEM.test(line)) {
                    if (!steps) {
                        steps = el('ol', 'hc-steps');
                        parts.push(steps);
                    }
                    steps.append(el('li', '', [el('span', 'hc-num', String(steps.children.length + 1)), el('span', '', line.replace(LIST_ITEM, ''))]));
                } else {
                    steps = null;
                    parts.push(el('p', '', line));
                }
            });
            return parts;
        };

        /** Pesan asisten; mengembalikan kolom untuk menempelkan aksi */
        const assistantMessage = (text, { sources = [], found = true, ai = false } = {}) => {
            const bubble = el('div', `hc-bubble hc-bubble-ai${found ? '' : ' hc-bubble-notfound'}`, [
                el('span', 'hc-label', [icon('sparkles'), ai ? t.label_ai : t.label_kb]),
                ...answerBody(text),
            ]);
            if (sources.length) {
                bubble.append(el('div', 'hc-sources', sources.map((s) => {
                    const a = el('a', 'hc-source', [icon('book-2'), s.name]);
                    a.href = s.url;
                    return a;
                })));
            }
            const col = el('div', 'hc-col', bubble);
            append(el('div', 'hc-row hc-row-ai', [el('span', 'hc-avatar', icon('sparkles')), col]));
            return col;
        };

        const typing = () => {
            const dots = el('div', 'hc-bubble hc-bubble-ai hc-typing', [el('span'), el('span'), el('span')]);
            dots.setAttribute('aria-label', t.typing);
            return append(el('div', 'hc-row hc-row-ai', [el('span', 'hc-avatar', icon('sparkles')), el('div', 'hc-col', dots)]));
        };

        // ---- Aksi di bawah jawaban terakhir -----------------------------------------------------

        const clearActions = () => thread.querySelectorAll('.hc-actions, .hc-offer').forEach((n) => n.remove());

        const lastQuestion = () => {
            const q = thread.querySelectorAll('.hc-bubble-user');
            return q.length ? q[q.length - 1].textContent : '';
        };

        /** "Apakah jawaban ini membantu?" → Masalah terselesaikan (rating) / Belum terselesaikan (kartu laporan) */
        const helpfulActions = (col) => {
            const box = el('div', 'hc-actions', [
                el('div', 'hc-actions-q', t.helpful),
                el('div', 'hc-actions-btns', [
                    button('hc-btn hc-btn-primary hc-btn-sm', [icon('circle-check'), t.resolved], () => ratingActions(box)),
                    button('hc-btn hc-btn-sm', t.not_resolved, () => { box.remove(); offerCard(col, t.offer); }),
                ]),
            ]);
            col.append(box);
            scrollDown();
        };

        const ratingActions = (box) => {
            const stars = [1, 2, 3, 4, 5].map((n) => {
                const s = button('hc-star', icon('star-filled'), async () => {
                    stars.forEach((x, i) => x.classList.toggle('active', i < n));
                    stars.forEach((x) => { x.disabled = true; });
                    const res = await post({ action: 'resolve', chat_id: chatId, rating: n });
                    if (res.ok) {
                        box.remove();
                        end(res.message);
                    } else {
                        systemMessage(res.message);
                        stars.forEach((x) => { x.disabled = false; });
                    }
                });
                s.setAttribute('aria-label', `${n}/5`);
                return s;
            });
            box.replaceChildren(el('div', 'hc-actions-q', t.rate), el('div', 'hc-stars', stars));
            scrollDown();
        };

        /** Kartu oranye bergaris putus-putus: tawarkan laporan berisi ringkasan percakapan */
        const offerCard = (col, text) => {
            clearActions();
            // Tanpa percakapan tersimpan (asisten tidak tersedia) → form laporan biasa
            const startReport = () => (chatId ? reportForm(card) : (window.location.href = root.dataset.reportUrl));
            const card = el('div', 'hc-offer', [
                el('p', '', text),
                el('div', 'hc-actions-btns', [
                    button('hc-btn hc-btn-primary hc-btn-sm', [icon('file-plus'), t.yes_report], startReport),
                    button('hc-btn hc-btn-sm', t.no_thanks, () => { card.remove(); input.focus(); }),
                ]),
            ]);
            col.append(card);
            scrollDown();
        };

        const reportForm = (card) => {
            const title = el('input', 'hc-input');
            title.type = 'text';
            title.maxLength = 200;
            title.minLength = 5;
            title.required = true;
            title.value = lastQuestion().slice(0, 80);
            title.setAttribute('aria-label', t.report_title);

            const summary = el('ul', 'hc-summary');
            thread.querySelectorAll('.hc-row-user .hc-bubble, .hc-row-ai:not([data-chat-greeting]) .hc-bubble-ai:not(.hc-typing)').forEach((b) => {
                const isUser = b.classList.contains('hc-bubble-user');
                const text = isUser ? b.textContent : [...b.querySelectorAll('p, li')].map((n) => n.textContent).join(' ');
                summary.append(el('li', '', [el('strong', '', `${isUser ? t.you : t.assistant}: `), text.trim().slice(0, 140)]));
            });
            const details = el('details', 'hc-summary-wrap', [el('summary', '', t.summary), summary]);

            const send = el('button', 'hc-btn hc-btn-primary hc-btn-sm', [icon('send'), t.send_report]);
            send.type = 'submit';
            const formEl = el('form', 'hc-report', [
                el('label', 'hc-field-label', t.report_title),
                title,
                details,
                el('div', 'hc-actions-btns', [send, button('hc-btn hc-btn-sm', t.cancel, () => card.remove())]),
            ]);
            formEl.addEventListener('submit', async (event) => {
                event.preventDefault();
                send.disabled = true;
                const res = await post({ action: 'ticket', chat_id: chatId, title: title.value.trim() });
                if (!res.ok) {
                    send.disabled = false;
                    systemMessage(res.message || t.error);
                    return;
                }
                const open = el('a', 'hc-btn hc-btn-primary hc-btn-sm', [icon('external-link'), t.open_ticket]);
                open.href = res.url;
                card.className = 'hc-success';
                card.replaceChildren(el('p', '', [icon('circle-check'), ' ', res.message]), open);
                end();
            });
            card.replaceChildren(formEl);
            title.focus();
            scrollDown();
        };

        /** Pasang aksi sesuai jenis jawaban terakhir */
        const attachActions = (col, found) => {
            if (ended) {
                return;
            }
            found ? helpfulActions(col) : offerCard(col, t.offer_notfound);
        };

        // ---- Alur percakapan ------------------------------------------------------------------

        const setBusy = (busy) => {
            input.disabled = busy || ended;
            form.querySelector('button').disabled = busy || ended;
            root.querySelectorAll('[data-chat-suggest]').forEach((b) => { b.disabled = busy || ended; });
        };

        const end = (note) => {
            ended = true;
            clearActions();
            if (note) {
                systemMessage(note);
            }
            setBusy(false);
        };

        const reset = () => {
            chatId = 0;
            ended = false;
            store.del(STORE_ID);
            thread.innerHTML = greeting;
            root.classList.remove('hc-started');
            setBusy(false);
            input.focus();
        };

        const send = async (text) => {
            text = text.trim();
            if (!text || input.disabled) {
                return;
            }
            input.value = '';
            clearActions();
            root.classList.add('hc-started');
            userMessage(text);
            const waiting = typing();
            setBusy(true);

            const res = await post({ action: 'message', chat_id: chatId, text });
            waiting.remove();
            setBusy(false);
            if (!res.ok) {
                const col = assistantMessage(res.message || t.error, { found: false });
                if (res.unavailable || !chatId) {
                    offerCard(col, t.error);
                }
                return;
            }
            chatId = res.chat_id;
            store.set(STORE_ID, String(chatId));
            if (res.masked) {
                systemMessage(t.masked);
            }
            attachActions(assistantMessage(res.answer, res), res.found);
            input.focus();
        };

        // Lanjutkan percakapan dari halaman sebelumnya (halaman penuh ↔ widget)
        if (chatId) {
            const res = await fetch(`${root.dataset.ajaxUrl}?action=history&chat_id=${chatId}`, { credentials: 'same-origin' }).then((r) => r.json()).catch(() => null);
            if (res?.ok && res.messages.length) {
                root.classList.add('hc-started');
                let lastCol = null;
                let lastFound = true;
                res.messages.forEach((m) => {
                    if (m.role === 'user') {
                        userMessage(m.text);
                    } else {
                        lastCol = assistantMessage(m.text, m);
                        lastFound = m.found;
                    }
                });
                if (res.status !== 'open') {
                    end(t.ended);
                } else if (lastCol) {
                    attachActions(lastCol, lastFound);
                }
            } else {
                reset();
            }
        }

        // ---- Kontrol ------------------------------------------------------------------------

        const toggle = (open) => {
            $('.hc-panel').hidden = !open;
            $('.hc-launcher').hidden = open;
            $('.hc-launcher').setAttribute('aria-expanded', String(open));
            store.set(STORE_OPEN, open ? '1' : '0');
            if (open) {
                input.focus();
                scrollDown();
            }
        };
        if (isWidget && store.get(STORE_OPEN) === '1') {
            toggle(true);
        }

        root.addEventListener('click', (event) => {
            const b = event.target.closest('[data-chat-toggle], [data-chat-new], [data-chat-suggest]');
            if (!b || !root.contains(b)) {
                return;
            }
            if (b.matches('[data-chat-toggle]')) {
                toggle($('.hc-panel').hidden);
            } else if (b.matches('[data-chat-new]')) {
                reset();
            } else {
                send(b.dataset.chatSuggest);
            }
        });

        form.addEventListener('submit', (event) => {
            event.preventDefault();
            send(input.value);
        });

        // Enter = kirim, Shift+Enter = baris baru
        input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                form.requestSubmit();
            }
        });

        if (!isWidget) {
            input.focus();
        }
    };

    const init = async () => {
        // Halaman penuh: pakai markup dari server, jangan muat widget melayang
        const page = document.querySelector('[data-halosis-chat="page"]');
        if (page) {
            if (page.querySelector('[data-chat-form]')) {
                mount(page);
            }
            return;
        }

        const html = await fetch(`${AJAX}?action=widget`, { credentials: 'same-origin' }).then((r) => (r.ok ? r.text() : '')).catch(() => '');
        if (!html.trim()) {
            return;
        }
        const holder = document.createElement('div');
        holder.innerHTML = html;
        const root = holder.firstElementChild;
        document.body.appendChild(root);
        mount(root);
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

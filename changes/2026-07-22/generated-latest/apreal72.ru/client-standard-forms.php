<?php
/**
 * Plugin Name: Client Standard Forms
 * Description: Unified callback and question forms requested by the client.
 */

if (!defined('ABSPATH')) {
    exit;
}

const CSF_DOMAIN = 'apreal72.ru';
const CSF_RECIPIENT = 'info@apreal72.ru';
const CSF_SENDER = 'info@apreal72.ru';
const CSF_SUCCESS = 'Спасибо за Ваше сообщение. Оно успешно отправлено';

function csf_clean_text($key)
{
    return isset($_POST[$key])
        ? sanitize_text_field(wp_unslash($_POST[$key]))
        : '';
}

function csf_send_form()
{
    check_ajax_referer('csf_submit', 'nonce');

    if (csf_clean_text('website') !== '') {
        wp_send_json_error(array('message' => 'Ошибка проверки формы.'), 400);
    }
    if (csf_clean_text('captcha') !== '5') {
        wp_send_json_error(array('message' => 'Введите цифру 5.'), 400);
    }

    $kind = csf_clean_text('kind');
    $page = esc_url_raw(isset($_POST['page']) ? wp_unslash($_POST['page']) : '');
    $headers = array(
        'Content-Type: text/html; charset=UTF-8',
        'From: ' . CSF_DOMAIN . ' <' . CSF_SENDER . '>',
    );

    if ($kind === 'callback') {
        $name = csf_clean_text('name');
        $phone = csf_clean_text('phone');
        if ($phone === '') {
            wp_send_json_error(array('message' => 'Введите телефон.'), 400);
        }
        $subject = 'ЗАКАЗАТЬ ЗВОНОК — ' . CSF_DOMAIN;
        $message = '<p><strong>Имя:</strong> ' . esc_html($name) . '</p>';
        $message .= '<p><strong>Телефон:</strong> ' . esc_html($phone) . '</p>';
    } elseif ($kind === 'question') {
        $name = csf_clean_text('name');
        $phone = csf_clean_text('phone');
        $question = csf_clean_text('question');
        if ($phone === '') {
            wp_send_json_error(array('message' => 'Введите телефон.'), 400);
        }
        $subject = 'ЗАДАТЬ ВОПРОС — ' . CSF_DOMAIN;
        $message = '<p><strong>Имя:</strong> ' . esc_html($name) . '</p>';
        $message .= '<p><strong>Телефон:</strong> ' . esc_html($phone) . '</p>';
        if ($question !== '') {
            $message .= '<p><strong>Вопрос:</strong><br>' . nl2br(esc_html($question)) . '</p>';
        }
    } else {
        wp_send_json_error(array('message' => 'Неизвестная форма.'), 400);
    }

    $message .= '<p><strong>Страница:</strong> ' . esc_html($page) . '</p>';
    $sent = wp_mail(CSF_RECIPIENT, $subject, $message, $headers);
    if (!$sent) {
        wp_send_json_error(
            array('message' => 'Не удалось отправить сообщение. Попробуйте еще раз.'),
            500
        );
    }
    wp_send_json_success(array('message' => CSF_SUCCESS));
}
add_action('wp_ajax_nopriv_csf_send_form', 'csf_send_form');
add_action('wp_ajax_csf_send_form', 'csf_send_form');



function csf_render_forms()
{
    if (is_admin()) {
        return;
    }
    $endpoint = admin_url('admin-ajax.php');
    $nonce = wp_create_nonce('csf_submit');
    ?>
    <div class="csf-root" data-endpoint="<?php echo esc_url($endpoint); ?>">
        <div class="csf-actions" aria-label="Формы связи">
            <button type="button" class="csf-action csf-open-callback">ЗАКАЗАТЬ ЗВОНОК</button>
            <button type="button" class="csf-action csf-action-secondary csf-open-question">ЗАДАТЬ ВОПРОС</button>
        </div>
        <div class="csf-overlay" hidden></div>
        <section class="csf-modal" data-modal="callback" role="dialog" aria-modal="true" aria-labelledby="csf-callback-title" hidden>
            <button type="button" class="csf-close" aria-label="Закрыть">&times;</button>
            <h2 id="csf-callback-title">ЗАКАЗАТЬ ЗВОНОК</h2>
            <form class="csf-form">
                <input type="hidden" name="action" value="csf_send_form">
                <input type="hidden" name="nonce" value="<?php echo esc_attr($nonce); ?>">
                <input type="hidden" name="kind" value="callback">
                <input type="hidden" name="page" value="">
                <input class="csf-honeypot" type="text" name="website" tabindex="-1" autocomplete="off">
                <label>Имя <span class="csf-optional">(необязательно)</span><input type="text" name="name" autocomplete="name" placeholder="Имя"></label>
                <label>Телефон<input type="tel" name="phone" required autocomplete="tel" placeholder="+7 (___) ___-__-__"></label>
                <label>Введите цифрами: пять<input type="text" name="captcha" required inputmode="numeric" autocomplete="off"></label>
                <p class="csf-consent">Нажимая на кнопку "Отправить" я даю согласие на обработку персональных данных на условиях <a href="https://www.apreal.ru/konfedencialnost.html" target="_blank" rel="noopener noreferrer">Политики обработки персональных данных</a></p>
                <button class="csf-submit" type="submit">Отправить</button>
                <p class="csf-result" aria-live="polite"></p>
            </form>
        </section>
        <section class="csf-modal" data-modal="question" role="dialog" aria-modal="true" aria-labelledby="csf-question-title" hidden>
            <button type="button" class="csf-close" aria-label="Закрыть">&times;</button>
            <h2 id="csf-question-title">ЗАДАТЬ ВОПРОС</h2>
            <form class="csf-form">
                <input type="hidden" name="action" value="csf_send_form">
                <input type="hidden" name="nonce" value="<?php echo esc_attr($nonce); ?>">
                <input type="hidden" name="kind" value="question">
                <input type="hidden" name="page" value="">
                <input class="csf-honeypot" type="text" name="website" tabindex="-1" autocomplete="off">
                <label>Имя <span class="csf-optional">(необязательно)</span><input type="text" name="name" autocomplete="name" placeholder="Имя"></label>
                <label>Телефон<input type="tel" name="phone" required autocomplete="tel" placeholder="+7 (___) ___-__-__"></label>
                <label>Ваш вопрос <span class="csf-optional">(необязательно)</span><textarea name="question" rows="4"></textarea></label>
                <label>Введите цифрами: пять<input type="text" name="captcha" required inputmode="numeric" autocomplete="off"></label>
                <p class="csf-consent">Нажимая на кнопку "Отправить" я даю согласие на обработку персональных данных на условиях <a href="https://www.apreal.ru/konfedencialnost.html" target="_blank" rel="noopener noreferrer">Политики обработки персональных данных</a></p>
                <button class="csf-submit" type="submit">Отправить</button>
                <p class="csf-result" aria-live="polite"></p>
            </form>
        </section>
    </div>
    <style>
    .csf-actions{display:none!important}html.client-contact-modal-open body > jdiv{display:none!important}.csf-root,.csf-root *{box-sizing:border-box}.csf-actions{position:fixed;right:96px;bottom:16px;z-index:2147483600;display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:calc(100vw - 112px)}.csf-action,.csf-submit{border:0;border-radius:4px;background:#c62828;color:#fff;padding:12px 16px;font:700 14px/1.2 Arial,sans-serif;letter-spacing:0;cursor:pointer;box-shadow:0 3px 12px rgba(0,0,0,.22)}.csf-action-secondary{background:#263238}.csf-overlay{position:fixed;inset:0;z-index:2147483601;background:rgba(0,0,0,.62)}.csf-modal{position:fixed;z-index:2147483602;left:50%;top:50%;transform:translate(-50%,-50%);width:min(520px,calc(100vw - 28px));max-height:calc(100vh - 28px);overflow:auto;background:#fff;color:#222;padding:28px;border-radius:6px;box-shadow:0 12px 50px rgba(0,0,0,.4);font-family:Arial,sans-serif}.csf-overlay[hidden],.csf-modal[hidden]{display:none!important}.csf-modal h2{margin:0 42px 22px 0;font:700 24px/1.2 Arial,sans-serif;letter-spacing:0;color:#222}.csf-close{position:absolute;right:12px;top:8px;width:38px;height:38px;border:0;background:transparent;color:#111;font:700 34px/34px Arial,sans-serif;cursor:pointer}.csf-form{display:grid;gap:14px}.csf-form label{display:grid;gap:6px;font:600 14px/1.3 Arial,sans-serif;color:#222}.csf-form input,.csf-form textarea{width:100%;border:1px solid #999;border-radius:3px;background:#fff;color:#111;padding:11px 12px;font:400 16px/1.3 Arial,sans-serif;letter-spacing:0}.csf-form textarea{resize:vertical}.csf-consent{margin:0;font:400 12px/1.45 Arial,sans-serif;color:#444}.csf-consent a{color:#0b57d0;text-decoration:underline}.csf-optional{font-weight:400;color:#666}.csf-result{display:none;margin:0;padding:10px;border:1px solid #2e7d32;color:#1b5e20;font:600 14px/1.4 Arial,sans-serif}.csf-result.is-visible{display:block}.csf-result.is-error{border-color:#c62828;color:#b71c1c}.csf-honeypot{position:absolute!important;left:-10000px!important;width:1px!important;height:1px!important;opacity:0!important}.csf-submit[disabled]{opacity:.65;cursor:wait}@media(max-width:560px){.csf-actions{left:10px;right:72px;bottom:10px;display:grid;grid-template-columns:1fr 1fr;max-width:none}.csf-action{padding:11px 8px;font-size:12px}.csf-modal{padding:22px 18px}.csf-modal h2{font-size:20px}}
    </style>
    <script>
    document.addEventListener('DOMContentLoaded',function(){var root=document.querySelector('.csf-root');if(!root)return;if(root.parentNode!==document.body)document.body.appendChild(root);var overlay=root.querySelector('.csf-overlay');var modals=root.querySelectorAll('.csf-modal');function closeAll(){overlay.hidden=true;modals.forEach(function(modal){modal.hidden=true;});document.documentElement.style.overflow='';document.documentElement.classList.remove('client-contact-modal-open');}function openModal(kind){closeAll();var modal=root.querySelector('[data-modal="'+kind+'"]');if(!modal)return;overlay.hidden=false;modal.hidden=false;document.documentElement.style.overflow='hidden';document.documentElement.classList.add('client-contact-modal-open');var field=modal.querySelector('input:not([type="hidden"]):not(.csf-honeypot)');if(field)field.focus();}root.querySelectorAll('.csf-open-callback').forEach(function(el){el.addEventListener('click',function(){openModal('callback');});});root.querySelectorAll('.csf-open-question').forEach(function(el){el.addEventListener('click',function(){openModal('question');});});root.querySelectorAll('.csf-close').forEach(function(el){el.addEventListener('click',closeAll);});overlay.addEventListener('click',closeAll);document.addEventListener('keydown',function(event){if(event.key==='Escape')closeAll();});var callbackLabels=['заказать звонок','обратный звонок','перезвонить','бесплатная консультация','получить бесплатную консультацию','оставить заявку'];var questionLabels=['задать вопрос','расчет стоимости','расчёт стоимости','узнать цену'];[['a[href="#phone-modal"]','callback','ЗАКАЗАТЬ ЗВОНОК'],['a[href="#license-modal"]','question','ЗАДАТЬ ВОПРОС'],['a[href="#back-modal"]','question','ЗАДАТЬ ВОПРОС']].forEach(function(item){document.querySelectorAll(item[0]).forEach(function(el){if(el.dataset.csfBound==='1')return;el.dataset.csfBound='1';if(el.tagName==='INPUT')el.value=item[2];else el.textContent=item[2];el.setAttribute('role','button');el.setAttribute('tabindex','0');function activate(event){event.preventDefault();event.stopImmediatePropagation();openModal(item[1]);}el.addEventListener('click',activate,true);el.addEventListener('keydown',function(event){if(event.key==='Enter'||event.key===' '){activate(event);}},true);});});document.querySelectorAll('a,button,[role="button"],input[type="button"]').forEach(function(el){if(el.dataset.csfBound==='1')return;if(el.closest('.csf-root')||el.closest('form'))return;var raw=el.tagName==='INPUT'?el.value:el.textContent;var label=(raw||'').replace(/\s+/g,' ').trim().toLowerCase();if(!label||label.length>90)return;var kind='';if(questionLabels.some(function(x){return label.indexOf(x)!==-1;}))kind='question';else if(callbackLabels.some(function(x){return label.indexOf(x)!==-1;}))kind='callback';if(!kind)return;if(el.tagName==='INPUT')el.value=kind==='callback'?'ЗАКАЗАТЬ ЗВОНОК':'ЗАДАТЬ ВОПРОС';else el.textContent=kind==='callback'?'ЗАКАЗАТЬ ЗВОНОК':'ЗАДАТЬ ВОПРОС';el.addEventListener('click',function(event){event.preventDefault();event.stopImmediatePropagation();openModal(kind);},true);});root.querySelectorAll('.csf-form').forEach(function(form){form.addEventListener('submit',function(event){event.preventDefault();var submit=form.querySelector('.csf-submit');var result=form.querySelector('.csf-result');var page=form.querySelector('[name="page"]');page.value=window.location.href;result.className='csf-result';result.textContent='';submit.disabled=true;fetch(root.dataset.endpoint,{method:'POST',body:new FormData(form),credentials:'same-origin'}).then(function(response){return response.json().then(function(payload){return {ok:response.ok,payload:payload};});}).then(function(outcome){var payload=outcome.payload;var message=payload&&payload.data&&payload.data.message?payload.data.message:'Не удалось отправить сообщение.';if(!outcome.ok||!payload.success)throw new Error(message);result.textContent=message;result.classList.add('is-visible');form.reset();}).catch(function(error){result.textContent=error.message||'Не удалось отправить сообщение.';result.classList.add('is-visible','is-error');}).finally(function(){submit.disabled=false;});});});});
    </script>
    <?php
}
add_action('wp_footer', 'csf_render_forms', 1000);

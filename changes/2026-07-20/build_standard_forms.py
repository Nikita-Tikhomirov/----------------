#!/usr/bin/env python3
"""Generate the standardized application forms for remaining client sites."""

from __future__ import annotations

import argparse
from pathlib import Path


CONSENT_TEXT = (
    'Нажимая на кнопку "Отправить" я даю согласие на обработку '
    "персональных данных на условиях Политики обработки персональных данных"
)
POLICY_URL = "https://www.apreal.ru/konfedencialnost.html"
SUCCESS_MESSAGE = "Спасибо за Ваше сообщение. Оно успешно отправлено"

EXCLUDED = {
    "rectavr.ru",
    "fstek.spb.ru",
    "lic-k.ru",
    "apreal-samara.ru",
    "ed-krd.ru",
}

# Keep the domain mailbox as the primary recipient and add a direct copy where
# fresh live submissions did not reach the client's central inbox.
CENTRAL_COPY_SITES = {
    "39mchs.ru",
    "docp.ru",
    "dpomuc.ru",
    "ed-kgd.ru",
    "minkult78.ru",
    "muc-vrn.ru",
    "nousro.ru",
    "nousro-nn.ru",
}

# These domains accepted Bcc submissions but did not place the central copy in
# the mailbox. Keep the site mailbox primary and require a second direct send.
SEPARATE_CENTRAL_COPY_SITES = {
    "39mchs.ru",
    "muc-vrn.ru",
}

WORDPRESS_SITES = {
    "docp.ru": "info@docp.ru",
    "elecktro.ru": "info@elecktro.ru",
    "medlic.spb.ru": "info@medlic.spb.ru",
    "mchs-spb.ru": "info@mchs-spb.ru",
    "otxodi.ru": "info@otxodi.ru",
    "apreal.spb.ru": "spb@apreal.ru",
    "minkult78.ru": "info@minkult78.ru",
    "medtex78.ru": "info@medtex78.ru",
    "mchs78.ru": "info@mchs78.ru",
    "license39.ru": "info@license39.ru",
    "39mchs.ru": "info@39mchs.ru",
    "apreal-nn.ru": "info@apreal-nn.ru",
    "apreal-volgograd.ru": "vlg-ap@bk.ru",
    "apreal72.ru": "info@apreal72.ru",
    "nousro.ru": "info@nousro.ru",
    "dpomuc.ru": "info@dpomuc.ru",
    "ed-kgd.ru": "info@ed-kgd.ru",
    "muc-vrn.ru": "info@muc-vrn.ru",
    "nousro-nn.ru": "info@nousro-nn.ru",
}

STATIC_SITES = {
    "fste.ru": "info@fste.ru",
    "lfsb.ru": "info@lfsb.ru",
    "medtex39.ru": "info@medtex39.ru",
    "shopap.ru": "info@shopap.ru",
}

LEGACY_CF7_FORMS = {
    "apreal-volgograd.ru": (3261, 3317, 3497),
}

HIDDEN_STANDARD_ACTIONS = {
    "39mchs.ru",
    "ed-kgd.ru",
    "medtex78.ru",
    "minkult78.ru",
    "nousro.ru",
}

INLINE_STANDARD_ACTIONS = {
    "apreal-volgograd.ru",
    "docp.ru",
    "dpomuc.ru",
    "elecktro.ru",
    "mchs78.ru",
}


WORDPRESS_TEMPLATE = r"""<?php
/**
 * Plugin Name: Client Standard Forms
 * Description: Unified callback and question forms requested by the client.
 */

if (!defined('ABSPATH')) {
    exit;
}

const CSF_DOMAIN = '__DOMAIN__';
const CSF_RECIPIENT = '__RECIPIENT__';
const CSF_SENDER = 'wordpress@__DOMAIN__';
const CSF_SUCCESS = '__SUCCESS__';

function csf_set_envelope_sender($phpmailer)
{
    $phpmailer->Sender = $phpmailer->From;
}

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
        'Reply-To: ' . CSF_SENDER,
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
    add_action('phpmailer_init', 'csf_set_envelope_sender', 999);
    $sent = wp_mail(CSF_RECIPIENT, $subject, $message, $headers);
    remove_action('phpmailer_init', 'csf_set_envelope_sender', 999);
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

function csf_refresh_nonce()
{
    nocache_headers();
    wp_send_json_success(array('nonce' => wp_create_nonce('csf_submit')));
}
add_action('wp_ajax_nopriv_csf_refresh_nonce', 'csf_refresh_nonce');
add_action('wp_ajax_csf_refresh_nonce', 'csf_refresh_nonce');

__LEGACY_CF7_PROTECTION__

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
                <p class="csf-consent">Нажимая на кнопку "Отправить" я даю согласие на обработку персональных данных на условиях <a href="__POLICY__" target="_blank" rel="noopener noreferrer">Политики обработки персональных данных</a></p>
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
                <p class="csf-consent">Нажимая на кнопку "Отправить" я даю согласие на обработку персональных данных на условиях <a href="__POLICY__" target="_blank" rel="noopener noreferrer">Политики обработки персональных данных</a></p>
                <button class="csf-submit" type="submit">Отправить</button>
                <p class="csf-result" aria-live="polite"></p>
            </form>
        </section>
    </div>
    <style>
    html.client-contact-modal-open body > jdiv{display:none!important}.csf-root,.csf-root *{box-sizing:border-box}.csf-actions{position:fixed;right:96px;bottom:16px;z-index:2147483600;display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:calc(100vw - 112px)}.csf-action,.csf-submit{border:0;border-radius:4px;background:#c62828;color:#fff;padding:12px 16px;font:700 14px/1.2 Arial,sans-serif;letter-spacing:0;cursor:pointer;box-shadow:0 3px 12px rgba(0,0,0,.22)}.csf-action-secondary{background:#263238}.csf-overlay{position:fixed;inset:0;z-index:2147483601;background:rgba(0,0,0,.62)}.csf-modal{position:fixed;z-index:2147483602;left:50%;top:50%;transform:translate(-50%,-50%);width:min(520px,calc(100vw - 28px));max-height:calc(100vh - 28px);overflow:auto;background:#fff;color:#222;padding:28px;border-radius:6px;box-shadow:0 12px 50px rgba(0,0,0,.4);font-family:Arial,sans-serif}.csf-overlay[hidden],.csf-modal[hidden]{display:none!important}.csf-modal h2{margin:0 42px 22px 0;font:700 24px/1.2 Arial,sans-serif;letter-spacing:0;color:#222}.csf-close{position:absolute;right:12px;top:8px;width:38px;height:38px;border:0;background:transparent;color:#111;font:700 34px/34px Arial,sans-serif;cursor:pointer}.csf-form{display:grid;gap:14px}.csf-form label{display:grid;gap:6px;font:600 14px/1.3 Arial,sans-serif;color:#222}.csf-form input,.csf-form textarea{width:100%;border:1px solid #999;border-radius:3px;background:#fff;color:#111;padding:11px 12px;font:400 16px/1.3 Arial,sans-serif;letter-spacing:0}.csf-form textarea{resize:vertical}.csf-consent{margin:0;font:400 12px/1.45 Arial,sans-serif;color:#444}.csf-consent a{color:#0b57d0;text-decoration:underline}.csf-optional{font-weight:400;color:#666}.csf-result{display:none;margin:0;padding:10px;border:1px solid #2e7d32;color:#1b5e20;font:600 14px/1.4 Arial,sans-serif}.csf-result.is-visible{display:block}.csf-result.is-error{border-color:#c62828;color:#b71c1c}.csf-inline-result{display:none;clear:both;margin:10px 0 0;padding:8px 10px;border:1px solid #2e7d32;background:#fff;color:#1b5e20;font:600 14px/1.35 Arial,sans-serif}.csf-inline-result.is-visible{display:block}.csf-inline-result.is-error{border-color:#c62828;color:#b71c1c}.csf-honeypot{position:absolute!important;left:-10000px!important;width:1px!important;height:1px!important;opacity:0!important}.csf-submit[disabled]{opacity:.65;cursor:wait}@media(max-width:560px){.csf-actions{left:10px;right:72px;bottom:10px;display:grid;grid-template-columns:1fr 1fr;max-width:none}.csf-action{padding:11px 8px;font-size:12px}.csf-modal{padding:22px 18px}.csf-modal h2{font-size:20px}}
    </style>
    <script>
    document.addEventListener('DOMContentLoaded',function(){var root=document.querySelector('.csf-root');if(!root)return;if(root.parentNode!==document.body)document.body.appendChild(root);var overlay=root.querySelector('.csf-overlay');var modals=root.querySelectorAll('.csf-modal');function closeAll(){overlay.hidden=true;modals.forEach(function(modal){modal.hidden=true;});document.documentElement.style.overflow='';document.documentElement.classList.remove('client-contact-modal-open');}function openModal(kind){closeAll();var modal=root.querySelector('[data-modal="'+kind+'"]');if(!modal)return;overlay.hidden=false;modal.hidden=false;document.documentElement.style.overflow='hidden';document.documentElement.classList.add('client-contact-modal-open');var field=modal.querySelector('input:not([type="hidden"]):not(.csf-honeypot)');if(field)field.focus();}function parseResponse(response){return response.text().then(function(text){var payload=null;try{payload=JSON.parse(text);}catch(error){}return {response:response,payload:payload,text:text};});}function refreshNonce(){var data=new URLSearchParams();data.set('action','csf_refresh_nonce');return fetch(root.dataset.endpoint,{method:'POST',body:data,credentials:'same-origin',cache:'no-store'}).then(parseResponse).then(function(outcome){var nonce=outcome.payload&&outcome.payload.success&&outcome.payload.data?outcome.payload.data.nonce:'';if(!nonce)throw new Error('Не удалось обновить форму. Перезагрузите страницу.');return nonce;});}function submitStandardPayload(payload,attempt){return fetch(root.dataset.endpoint,{method:'POST',body:payload,credentials:'same-origin'}).then(parseResponse).then(function(outcome){var response=outcome.response;if(response.status===403&&attempt===0)return refreshNonce().then(function(nonce){payload.set('nonce',nonce);root.querySelectorAll('[name="nonce"]').forEach(function(field){field.value=nonce;});return submitStandardPayload(payload,1);});return outcome;});}function messageFrom(outcome){return outcome.payload&&outcome.payload.data&&outcome.payload.data.message?outcome.payload.data.message:'Не удалось отправить сообщение.';}root.querySelectorAll('.csf-open-callback').forEach(function(el){el.addEventListener('click',function(){openModal('callback');});});root.querySelectorAll('.csf-open-question').forEach(function(el){el.addEventListener('click',function(){openModal('question');});});root.querySelectorAll('.csf-close').forEach(function(el){el.addEventListener('click',closeAll);});overlay.addEventListener('click',closeAll);document.addEventListener('keydown',function(event){if(event.key==='Escape')closeAll();});var callbackLabels=['заказать звонок','обратный звонок','перезвонить','бесплатная консультация','получить бесплатную консультацию','оставить заявку'];var questionLabels=['задать вопрос','расчет стоимости','расчёт стоимости','узнать цену'];document.querySelectorAll('a,button,[role="button"],input[type="button"]').forEach(function(el){if(el.closest('.csf-root')||el.closest('form'))return;var raw=el.tagName==='INPUT'?el.value:el.textContent;var label=(raw||'').replace(/\s+/g,' ').trim().toLowerCase();if(!label||label.length>90)return;var kind='';if(questionLabels.some(function(x){return label.indexOf(x)!==-1;}))kind='question';else if(callbackLabels.some(function(x){return label.indexOf(x)!==-1;}))kind='callback';if(!kind)return;if(el.tagName==='INPUT')el.value=kind==='callback'?'ЗАКАЗАТЬ ЗВОНОК':'ЗАДАТЬ ВОПРОС';else el.textContent=kind==='callback'?'ЗАКАЗАТЬ ЗВОНОК':'ЗАДАТЬ ВОПРОС';el.addEventListener('click',function(event){event.preventDefault();event.stopImmediatePropagation();openModal(kind);},true);});function bindLegacyPhoneForms(){document.querySelectorAll('input[name="form-action"][value="phone"]').forEach(function(marker){var legacyPhoneForm=marker.form;if(!legacyPhoneForm||legacyPhoneForm.dataset.csfBound==='1')return;legacyPhoneForm.dataset.csfBound='1';legacyPhoneForm.classList.add('csf-legacy-phone-form');var result=document.createElement('p');result.className='csf-inline-result';result.setAttribute('aria-live','polite');legacyPhoneForm.appendChild(result);legacyPhoneForm.addEventListener('submit',function(event){event.preventDefault();event.stopImmediatePropagation();var submit=legacyPhoneForm.querySelector('[type="submit"]');var payload=new FormData();payload.set('action','csf_send_form');payload.set('nonce',root.querySelector('[name="nonce"]').value);payload.set('kind','callback');payload.set('page',window.location.href);payload.set('website','');payload.set('name',(legacyPhoneForm.querySelector('[name="phone-name"]')||{}).value||'');payload.set('phone',(legacyPhoneForm.querySelector('[name="phone-phone"]')||{}).value||'');payload.set('captcha','5');result.className='csf-inline-result';result.textContent='';if(submit)submit.disabled=true;submitStandardPayload(payload,0).then(function(outcome){var message=messageFrom(outcome);if(!outcome.response.ok||!outcome.payload||!outcome.payload.success)throw new Error(message);result.textContent=message;result.classList.add('is-visible');legacyPhoneForm.reset();}).catch(function(error){result.textContent=error.message||'Не удалось отправить сообщение.';result.classList.add('is-visible','is-error');}).finally(function(){if(submit)submit.disabled=false;});},true);});}bindLegacyPhoneForms();root.querySelectorAll('.csf-form').forEach(function(form){form.addEventListener('submit',function(event){event.preventDefault();var submit=form.querySelector('.csf-submit');var result=form.querySelector('.csf-result');var page=form.querySelector('[name="page"]');page.value=window.location.href;result.className='csf-result';result.textContent='';submit.disabled=true;submitStandardPayload(new FormData(form),0).then(function(outcome){var message=messageFrom(outcome);if(!outcome.response.ok||!outcome.payload||!outcome.payload.success)throw new Error(message);result.textContent=message;result.classList.add('is-visible');form.reset();}).catch(function(error){result.textContent=error.message||'Не удалось отправить сообщение.';result.classList.add('is-visible','is-error');}).finally(function(){submit.disabled=false;});});});});
    </script>
    <?php
}
add_action('wp_footer', 'csf_render_forms', 1000);
"""


STATIC_HANDLER_TEMPLATE = r"""<?php
ini_set('display_errors', '0');
error_reporting(E_ALL);
header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store');

const CSF_DOMAIN = '__DOMAIN__';
const CSF_RECIPIENT = '__RECIPIENT__';
const CSF_SENDER = 'wordpress@__DOMAIN__';
const CSF_SUCCESS = '__SUCCESS__';

function respond($success, $message, $status = 200)
{
    http_response_code($status);
    echo json_encode(array('success' => $success, 'message' => $message), JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond(false, 'Метод не поддерживается.', 405);
}
if (trim(isset($_POST['website']) ? (string) $_POST['website'] : '') !== '') {
    respond(false, 'Ошибка проверки формы.', 400);
}
if (trim(isset($_POST['captcha']) ? (string) $_POST['captcha'] : '') !== '5') {
    respond(false, 'Введите цифру 5.', 400);
}

$kind = isset($_POST['kind']) ? trim((string) $_POST['kind']) : '';
$page = isset($_POST['page']) ? filter_var((string) $_POST['page'], FILTER_SANITIZE_URL) : '';
$headers = array(
    'MIME-Version: 1.0',
    'Content-Type: text/html; charset=UTF-8',
    'From: ' . CSF_DOMAIN . ' <' . CSF_SENDER . '>',
    'Reply-To: ' . CSF_SENDER,
);

if ($kind === 'callback') {
    $name = isset($_POST['name']) ? trim(strip_tags((string) $_POST['name'])) : '';
    $phone = isset($_POST['phone']) ? trim(strip_tags((string) $_POST['phone'])) : '';
    if ($phone === '') {
        respond(false, 'Введите телефон.', 400);
    }
    $subject = 'ЗАКАЗАТЬ ЗВОНОК — ' . CSF_DOMAIN;
    $message = '<p><strong>Имя:</strong> ' . htmlspecialchars($name, ENT_QUOTES, 'UTF-8') . '</p>';
    $message .= '<p><strong>Телефон:</strong> ' . htmlspecialchars($phone, ENT_QUOTES, 'UTF-8') . '</p>';
} elseif ($kind === 'question') {
    $name = isset($_POST['name']) ? trim(strip_tags((string) $_POST['name'])) : '';
    $phone = isset($_POST['phone']) ? trim(strip_tags((string) $_POST['phone'])) : '';
    $question = isset($_POST['question']) ? trim(strip_tags((string) $_POST['question'])) : '';
    if ($phone === '') {
        respond(false, 'Введите телефон.', 400);
    }
    $subject = 'ЗАДАТЬ ВОПРОС — ' . CSF_DOMAIN;
    $message = '<p><strong>Имя:</strong> ' . htmlspecialchars($name, ENT_QUOTES, 'UTF-8') . '</p>';
    $message .= '<p><strong>Телефон:</strong> ' . htmlspecialchars($phone, ENT_QUOTES, 'UTF-8') . '</p>';
    if ($question !== '') {
        $message .= '<p><strong>Вопрос:</strong><br>' . nl2br(htmlspecialchars($question, ENT_QUOTES, 'UTF-8')) . '</p>';
    }
} else {
    respond(false, 'Неизвестная форма.', 400);
}

$message .= '<p><strong>Страница:</strong> ' . htmlspecialchars($page, ENT_QUOTES, 'UTF-8') . '</p>';
$sent = mail(
    CSF_RECIPIENT,
    $subject,
    $message,
    implode("\r\n", $headers),
    '-f' . CSF_SENDER
);
respond(
    $sent,
    $sent ? CSF_SUCCESS : 'Не удалось отправить сообщение. Попробуйте еще раз.',
    $sent ? 200 : 500
);
"""


MEDTEX39_HANDLER_TEMPLATE = r"""<?php
ini_set('display_errors', '0');
error_reporting(E_ALL);
header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

const CSF_DOMAIN = '__DOMAIN__';
const CSF_RECIPIENT = '__RECIPIENT__';
const CSF_SENDER = 'wordpress@__DOMAIN__';
const CSF_SUCCESS = '__SUCCESS__';
const CSF_TOKEN_MIN_AGE = 2;
const CSF_TOKEN_MAX_AGE = 1800;
const CSF_RATE_SECONDS = 30;

session_name('medtex39_form');
session_set_cookie_params(CSF_TOKEN_MAX_AGE, '/', '', true, true);
session_start();

function respond($success, $message, $status = 200, $extra = array())
{
    http_response_code($status);
    $payload = array('success' => $success, 'message' => $message);
    foreach ($extra as $key => $value) {
        $payload[$key] = $value;
    }
    echo json_encode($payload, JSON_UNESCAPED_UNICODE);
    exit;
}

function clean_value($name)
{
    if (!isset($_POST[$name]) || is_array($_POST[$name])) {
        return '';
    }
    return trim(strip_tags((string) $_POST[$name]));
}

function issue_challenge()
{
    $bytes = function_exists('random_bytes')
        ? random_bytes(24)
        : openssl_random_pseudo_bytes(24);
    $token = bin2hex($bytes);
    $_SESSION['csf_form_token'] = $token;
    $_SESSION['csf_form_issued'] = time();
    respond(true, '', 200, array('token' => $token));
}

function verify_challenge()
{
    $provided = clean_value('form_token');
    $stored = isset($_SESSION['csf_form_token'])
        ? (string) $_SESSION['csf_form_token']
        : '';
    $issued = isset($_SESSION['csf_form_issued'])
        ? (int) $_SESSION['csf_form_issued']
        : 0;
    $age = time() - $issued;

    unset($_SESSION['csf_form_token'], $_SESSION['csf_form_issued']);
    if ($provided === '' || $stored === '' || !hash_equals($stored, $provided)) {
        respond(false, 'Обновите форму и повторите отправку.', 400);
    }
    if ($age < CSF_TOKEN_MIN_AGE) {
        respond(false, 'Подождите пару секунд и отправьте форму снова.', 429);
    }
    if ($age > CSF_TOKEN_MAX_AGE) {
        respond(false, 'Форма устарела. Откройте ее повторно.', 400);
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['challenge'])) {
    issue_challenge();
}
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond(false, 'Метод не поддерживается.', 405);
}

verify_challenge();
if (clean_value('website') !== '') {
    respond(false, 'Ошибка проверки формы.', 400);
}
if (clean_value('captcha') !== '5') {
    respond(false, 'Введите цифру 5.', 400);
}

$ip = isset($_SERVER['REMOTE_ADDR']) ? (string) $_SERVER['REMOTE_ADDR'] : 'unknown';
$rate_file = sys_get_temp_dir() . '/medtex39-csf-' . sha1($ip);
if (is_file($rate_file) && filemtime($rate_file) > time() - CSF_RATE_SECONDS) {
    respond(false, 'Подождите немного перед повторной отправкой.', 429);
}

$kind = clean_value('kind');
$page = isset($_POST['page'])
    ? filter_var((string) $_POST['page'], FILTER_SANITIZE_URL)
    : '';
$headers = array(
    'MIME-Version: 1.0',
    'Content-Type: text/html; charset=UTF-8',
    'From: ' . CSF_DOMAIN . ' <' . CSF_SENDER . '>',
    'Reply-To: ' . CSF_SENDER,
);

if ($kind === 'callback') {
    $name = clean_value('name');
    $phone = clean_value('phone');
    $phone_digits = preg_replace('/\D+/', '', $phone);
    if (strlen($phone_digits) < 7 || strlen($phone_digits) > 18) {
        respond(false, 'Введите корректный телефон.', 400);
    }
    $subject = 'ЗАКАЗАТЬ ЗВОНОК — ' . CSF_DOMAIN;
    $message = '<p><strong>Имя:</strong> '
        . htmlspecialchars($name, ENT_QUOTES, 'UTF-8') . '</p>';
    $message .= '<p><strong>Телефон:</strong> '
        . htmlspecialchars($phone, ENT_QUOTES, 'UTF-8') . '</p>';
} elseif ($kind === 'question') {
    $name = clean_value('name');
    $phone = clean_value('phone');
    $phone_digits = preg_replace('/\D+/', '', $phone);
    $question = clean_value('question');
    if (strlen($phone_digits) < 7 || strlen($phone_digits) > 18) {
        respond(false, 'Введите корректный телефон.', 400);
    }
    $subject = 'ЗАДАТЬ ВОПРОС — ' . CSF_DOMAIN;
    $message = '<p><strong>Имя:</strong> '
        . htmlspecialchars($name, ENT_QUOTES, 'UTF-8') . '</p>';
    $message .= '<p><strong>Телефон:</strong> '
        . htmlspecialchars($phone, ENT_QUOTES, 'UTF-8') . '</p>';
    if ($question !== '') {
        $message .= '<p><strong>Вопрос:</strong><br>'
            . nl2br(htmlspecialchars($question, ENT_QUOTES, 'UTF-8')) . '</p>';
    }
} else {
    respond(false, 'Неизвестная форма.', 400);
}

$message .= '<p><strong>Страница:</strong> '
    . htmlspecialchars($page, ENT_QUOTES, 'UTF-8') . '</p>';
$sent = mail(
    CSF_RECIPIENT,
    $subject,
    $message,
    implode("\r\n", $headers),
    '-f' . CSF_SENDER
);
if ($sent) {
    @touch($rate_file);
}
respond(
    $sent,
    $sent ? CSF_SUCCESS : 'Не удалось отправить сообщение. Попробуйте еще раз.',
    $sent ? 200 : 500
);
"""


STATIC_SCRIPT_TEMPLATE = r"""(function(){
if(document.querySelector('.csf-root'))return;
var policy='__POLICY__';
var success='__SUCCESS__';
var root=document.createElement('div');
root.className='csf-root';
root.innerHTML='<div class="csf-actions" aria-label="Формы связи"><button type="button" class="csf-action csf-open-callback">ЗАКАЗАТЬ ЗВОНОК</button><button type="button" class="csf-action csf-action-secondary csf-open-question">ЗАДАТЬ ВОПРОС</button></div><div class="csf-overlay" hidden></div><section class="csf-modal" data-modal="callback" role="dialog" aria-modal="true" hidden><button type="button" class="csf-close" aria-label="Закрыть">&times;</button><h2>ЗАКАЗАТЬ ЗВОНОК</h2><form class="csf-form"><input type="hidden" name="kind" value="callback"><input type="hidden" name="page"><input class="csf-honeypot" type="text" name="website" tabindex="-1" autocomplete="off"><label>Имя <span class="csf-optional">(необязательно)</span><input type="text" name="name" autocomplete="name" placeholder="Имя"></label><label>Телефон<input type="tel" name="phone" required autocomplete="tel" placeholder="+7 (___) ___-__-__"></label><label>Введите цифрами: пять<input type="text" name="captcha" required inputmode="numeric" autocomplete="off"></label><p class="csf-consent">Нажимая на кнопку "Отправить" я даю согласие на обработку персональных данных на условиях <a href="'+policy+'" target="_blank" rel="noopener noreferrer">Политики обработки персональных данных</a></p><button class="csf-submit" type="submit">Отправить</button><p class="csf-result" aria-live="polite"></p></form></section><section class="csf-modal" data-modal="question" role="dialog" aria-modal="true" hidden><button type="button" class="csf-close" aria-label="Закрыть">&times;</button><h2>ЗАДАТЬ ВОПРОС</h2><form class="csf-form"><input type="hidden" name="kind" value="question"><input type="hidden" name="page"><input class="csf-honeypot" type="text" name="website" tabindex="-1" autocomplete="off"><label>Имя <span class="csf-optional">(необязательно)</span><input type="text" name="name" autocomplete="name" placeholder="Имя"></label><label>Телефон<input type="tel" name="phone" required autocomplete="tel" placeholder="+7 (___) ___-__-__"></label><label>Ваш вопрос <span class="csf-optional">(необязательно)</span><textarea name="question" rows="4"></textarea></label><label>Введите цифрами: пять<input type="text" name="captcha" required inputmode="numeric" autocomplete="off"></label><p class="csf-consent">Нажимая на кнопку "Отправить" я даю согласие на обработку персональных данных на условиях <a href="'+policy+'" target="_blank" rel="noopener noreferrer">Политики обработки персональных данных</a></p><button class="csf-submit" type="submit">Отправить</button><p class="csf-result" aria-live="polite"></p></form></section>';
var style=document.createElement('style');
style.textContent='html.client-contact-modal-open body > jdiv{display:none!important}.csf-root,.csf-root *{box-sizing:border-box}.csf-actions{position:fixed;right:96px;bottom:16px;z-index:2147483600;display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:calc(100vw - 112px)}.csf-actions.csf-actions-sidebar{position:static;right:auto;bottom:auto;display:grid;grid-template-columns:1fr;margin:0 8px 14px;max-width:none}.csf-action,.csf-submit{border:0;border-radius:4px;background:#c62828;color:#fff;padding:12px 16px;font:700 14px/1.2 Arial,sans-serif;letter-spacing:0;cursor:pointer;box-shadow:0 3px 12px rgba(0,0,0,.22)}.csf-action-secondary{background:#263238}.csf-overlay{position:fixed;inset:0;z-index:2147483601;background:rgba(0,0,0,.62)}.csf-modal{position:fixed;z-index:2147483602;left:50%;top:50%;transform:translate(-50%,-50%);width:min(520px,calc(100vw - 28px));max-height:calc(100vh - 28px);overflow:auto;background:#fff;color:#222;padding:28px;border-radius:6px;box-shadow:0 12px 50px rgba(0,0,0,.4);font-family:Arial,sans-serif}.csf-overlay[hidden],.csf-modal[hidden]{display:none!important}.csf-modal h2{margin:0 42px 22px 0;font:700 24px/1.2 Arial,sans-serif;letter-spacing:0;color:#222}.csf-close{position:absolute;right:12px;top:8px;width:38px;height:38px;border:0;background:transparent;color:#111;font:700 34px/34px Arial,sans-serif;cursor:pointer}.csf-form{display:grid;gap:14px}.csf-form label{display:grid;gap:6px;font:600 14px/1.3 Arial,sans-serif;color:#222}.csf-form input,.csf-form textarea{width:100%;border:1px solid #999;border-radius:3px;background:#fff;color:#111;padding:11px 12px;font:400 16px/1.3 Arial,sans-serif;letter-spacing:0}.csf-form textarea{resize:vertical}.csf-consent{margin:0;font:400 12px/1.45 Arial,sans-serif;color:#444}.csf-consent a{color:#0b57d0;text-decoration:underline}.csf-optional{font-weight:400;color:#666}.csf-result{display:none;margin:0;padding:10px;border:1px solid #2e7d32;color:#1b5e20;font:600 14px/1.4 Arial,sans-serif}.csf-result.is-visible{display:block}.csf-result.is-error{border-color:#c62828;color:#b71c1c}.csf-honeypot{position:absolute!important;left:-10000px!important;width:1px!important;height:1px!important;opacity:0!important}.csf-submit[disabled]{opacity:.65;cursor:wait}@media(max-width:560px){.csf-actions:not(.csf-actions-sidebar){left:10px;right:72px;bottom:10px;display:grid;grid-template-columns:1fr 1fr;max-width:none}.csf-action{padding:11px 8px;font-size:12px}.csf-modal{padding:22px 18px}.csf-modal h2{font-size:20px}}';
document.head.appendChild(style);
document.body.appendChild(root);
var overlay=root.querySelector('.csf-overlay');var actions=root.querySelector('.csf-actions');var modals=root.querySelectorAll('.csf-modal');function closeAll(){overlay.hidden=true;modals.forEach(function(modal){modal.hidden=true;});document.documentElement.style.overflow='';document.documentElement.classList.remove('client-contact-modal-open');}function openModal(kind){closeAll();var modal=root.querySelector('[data-modal="'+kind+'"]');if(!modal)return;overlay.hidden=false;modal.hidden=false;document.documentElement.style.overflow='hidden';document.documentElement.classList.add('client-contact-modal-open');var field=modal.querySelector('input:not([type="hidden"]):not(.csf-honeypot)');if(field)field.focus();}root.querySelectorAll('.csf-open-callback').forEach(function(el){el.addEventListener('click',function(){openModal('callback');});});root.querySelectorAll('.csf-open-question').forEach(function(el){el.addEventListener('click',function(){openModal('question');});});root.querySelectorAll('.csf-close').forEach(function(el){el.addEventListener('click',closeAll);});overlay.addEventListener('click',closeAll);document.addEventListener('keydown',function(event){if(event.key==='Escape')closeAll();});var callbackLabels=['заказать звонок','обратный звонок','перезвонить','бесплатная консультация','получить бесплатную консультацию','оставить заявку','подать заявку'];var questionLabels=['задать вопрос','расчет стоимости','расчёт стоимости','узнать цену'];document.querySelectorAll('a,button,[role="button"],input[type="button"]').forEach(function(el){if(el.closest('.csf-root')||el.closest('form'))return;var raw=el.tagName==='INPUT'?el.value:el.textContent;var label=(raw||'').replace(/\s+/g,' ').trim().toLowerCase();if(!label||label.length>90)return;var kind='';if(questionLabels.some(function(x){return label.indexOf(x)!==-1;}))kind='question';else if(callbackLabels.some(function(x){return label.indexOf(x)!==-1;}))kind='callback';if(!kind)return;if(el.tagName==='INPUT')el.value=kind==='callback'?'ЗАКАЗАТЬ ЗВОНОК':'ЗАДАТЬ ВОПРОС';else el.textContent=kind==='callback'?'ЗАКАЗАТЬ ЗВОНОК':'ЗАДАТЬ ВОПРОС';el.addEventListener('click',function(event){event.preventDefault();event.stopImmediatePropagation();openModal(kind);},true);});var sidebar=document.querySelector('#leblok');if(sidebar&&actions){actions.classList.add('csf-actions-sidebar');sidebar.insertBefore(actions,sidebar.firstChild);}root.querySelectorAll('.csf-form').forEach(function(form){form.addEventListener('submit',function(event){event.preventDefault();var submit=form.querySelector('.csf-submit');var result=form.querySelector('.csf-result');form.querySelector('[name="page"]').value=window.location.href;result.className='csf-result';result.textContent='';submit.disabled=true;fetch('/client-standard-mail.php',{method:'POST',body:new FormData(form),credentials:'same-origin'}).then(function(response){return response.json().then(function(payload){return {ok:response.ok,payload:payload};});}).then(function(outcome){var message=outcome.payload&&outcome.payload.message?outcome.payload.message:'Не удалось отправить сообщение.';if(!outcome.ok||!outcome.payload.success)throw new Error(message);if(message!==success)message=success;result.textContent=message;result.classList.add('is-visible');form.reset();}).catch(function(error){result.textContent=error.message||'Не удалось отправить сообщение.';result.classList.add('is-visible','is-error');}).finally(function(){submit.disabled=false;});});});
})();
"""


def replace_contract(template: str, domain: str = "", recipient: str = "") -> str:
    return (
        template.replace("__DOMAIN__", domain)
        .replace("__RECIPIENT__", recipient)
        .replace("__CONSENT__", CONSENT_TEXT)
        .replace("__POLICY__", POLICY_URL)
        .replace("__SUCCESS__", SUCCESS_MESSAGE)
    )


def render_wordpress_plugin(domain: str, recipient: str) -> str:
    source = replace_contract(WORDPRESS_TEMPLATE, domain, recipient)
    if domain in CENTRAL_COPY_SITES:
        source = source.replace(
            f"const CSF_RECIPIENT = '{recipient}';",
            f"const CSF_RECIPIENT = '{recipient}';\n"
            "const CSF_CENTRAL_RECIPIENT = 'upreal@bk.ru';",
            1,
        )
        if domain in SEPARATE_CENTRAL_COPY_SITES:
            if domain == "39mchs.ru":
                central_send = (
                    "    $central_message = preg_replace('/<br\\s*\\/?>/i', \"\\n\", $message);\n"
                    "    $central_message = str_ireplace('</p>', \"\\n\", $central_message);\n"
                    "    $central_message = trim(wp_strip_all_tags($central_message));\n"
                    "    $central_headers = array(\n"
                    "        'From: ' . CSF_DOMAIN . ' <' . CSF_SENDER . '>',\n"
                    "        'Reply-To: ' . CSF_SENDER,\n"
                    "    );\n"
                    "    $central_sent = wp_mail(CSF_CENTRAL_RECIPIENT, $subject, $central_message, $central_headers);\n"
                )
            else:
                central_send = (
                    "    $central_sent = wp_mail(CSF_CENTRAL_RECIPIENT, $subject, $message, $headers);\n"
                )
            replacement = (
                central_send
                + "    $sent = wp_mail(CSF_RECIPIENT, $subject, $message, $headers);\n"
                + "    remove_action('phpmailer_init', 'csf_set_envelope_sender', 999);\n"
                "    if (!$sent || !$central_sent) {"
            )
            source = source.replace(
                "    $sent = wp_mail(CSF_RECIPIENT, $subject, $message, $headers);\n"
                "    remove_action('phpmailer_init', 'csf_set_envelope_sender', 999);\n"
                "    if (!$sent) {",
                replacement,
                1,
            )
        else:
            source = source.replace(
                "    );\n\n    if ($kind === 'callback') {",
                "    );\n"
                "    $headers[] = 'Bcc: ' . CSF_CENTRAL_RECIPIENT;\n\n"
                "    if ($kind === 'callback') {",
                1,
            )
    if domain in HIDDEN_STANDARD_ACTIONS:
        source = source.replace(
            '''        <div class="csf-actions" aria-label="Формы связи">
            <button type="button" class="csf-action csf-open-callback">ЗАКАЗАТЬ ЗВОНОК</button>
            <button type="button" class="csf-action csf-action-secondary csf-open-question">ЗАДАТЬ ВОПРОС</button>
        </div>
''',
            "",
            1,
        )
    if domain == "ed-kgd.ru":
        source = source.replace(
            "const CSF_SENDER = 'wordpress@ed-kgd.ru';",
            "const CSF_SENDER = 'wordpress@ed-kgd.ru';\n"
            "add_filter('show_admin_bar', '__return_false');\n\n"
            "function csf_disable_frontend_admin_bar()\n"
            "{\n"
            "    if (is_admin()) {\n"
            "        return;\n"
            "    }\n"
            "    show_admin_bar(false);\n"
            "    remove_action('wp_footer', 'wp_admin_bar_render', 1000);\n"
            "    remove_action('wp_head', '_admin_bar_bump_cb');\n"
            "}\n"
            "add_action('wp_loaded', 'csf_disable_frontend_admin_bar', PHP_INT_MAX);\n\n"
            "function csf_hide_frontend_admin_bar()\n"
            "{\n"
            "    if (!is_admin()) {\n"
            "        echo '<style>#wpadminbar{display:none!important}html{margin-top:0!important}</style>';\n"
            "    }\n"
            "}\n"
            "add_action('wp_head', 'csf_hide_frontend_admin_bar', PHP_INT_MAX);",
            1,
        )
    site_bindings = {
        "39mchs.ru": (
            (".js-feedback", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
            (".js-calculate", "question", "ЗАДАТЬ ВОПРОС"),
        ),
        "minkult78.ru": (
            (".js-feedback", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
            (".js-calculate", "question", "ЗАДАТЬ ВОПРОС"),
        ),
        "medtex78.ru": (
            (".js-feedback", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
            (".js-calculate", "question", "ЗАДАТЬ ВОПРОС"),
        ),
        "apreal.spb.ru": (
            (".phones .phones__callback", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
            (".ap-mobile-navs .phones__callback", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
            (".custom-slider .phones__callback", "question", "ЗАДАТЬ ВОПРОС"),
            (
                ".uk-width-expand\\\\@m.notForCopy .phones__callback",
                "question",
                "ЗАДАТЬ ВОПРОС",
            ),
            (".uk-width-1-6\\\\@m .uk-button-danger", "question", "ЗАДАТЬ ВОПРОС"),
        ),
        "license39.ru": (
            (".phones .phones__callback", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
            (".ap-mobile-navs .phones__callback", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
            (".custom-slider .phones__callback", "question", "ЗАДАТЬ ВОПРОС"),
            (".uk-width-1-6\\\\@m .uk-button-danger", "question", "ЗАДАТЬ ВОПРОС"),
        ),
        "apreal-nn.ru": (
            ('a[href="#phone-modal"]', "callback", "ЗАКАЗАТЬ ЗВОНОК"),
            ('a[href="#license-modal"]', "question", "ЗАДАТЬ ВОПРОС"),
            ('a[href="#back-modal"]', "question", "ЗАДАТЬ ВОПРОС"),
        ),
        "apreal72.ru": (
            ('a[href="#phone-modal"]', "callback", "ЗАКАЗАТЬ ЗВОНОК"),
            ('a[href="#license-modal"]', "question", "ЗАДАТЬ ВОПРОС"),
            ('a[href="#back-modal"]', "question", "ЗАДАТЬ ВОПРОС"),
        ),
        "medlic.spb.ru": (
            (
                ".client-form-actions a:first-child",
                "callback",
                "ЗАКАЗАТЬ ЗВОНОК",
            ),
            (
                ".client-form-actions a:last-child",
                "question",
                "ЗАДАТЬ ВОПРОС",
            ),
        ),
        "nousro.ru": (
            ("#mail-us", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
        ),
        "ed-kgd.ru": (
            ("#mail-us", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
        ),
        "muc-vrn.ru": (
            (".fixed-line-right a", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
            (
                '.full-navigation > a[href="#modal-full"]',
                "question",
                "ЗАДАТЬ ВОПРОС",
            ),
            (".mob-dop-btns a", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
        ),
        "nousro-nn.ru": (
            ("#mail-us", "callback", "ЗАКАЗАТЬ ЗВОНОК"),
        ),
    }.get(domain)
    if site_bindings:
        if recipient.lower().endswith("@" + domain.lower()):
            source = source.replace(
                f"const CSF_SENDER = 'wordpress@{domain}';",
                f"const CSF_SENDER = '{recipient}';",
                1,
            )
        source = source.replace(
            "html.client-contact-modal-open body > jdiv",
            ".csf-actions{display:none!important}html.client-contact-modal-open body > jdiv",
            1,
        )
        if domain == "medlic.spb.ru":
            source = source.replace(
                ".csf-actions{display:none!important}",
                ".csf-actions{display:none!important}"
                "#n2-ss-2.n2-ss-load-fade.n2-ss-loaded{opacity:1!important}",
                1,
            )
        if domain in ("apreal-nn.ru", "apreal72.ru"):
            source = source.replace(
                ".csf-actions{display:none!important}",
                '.csf-actions{display:none!important}'
                "@media(max-width:560px){html,body{max-width:100%;overflow-x:hidden}"
                "#primary-menu{width:100%!important;min-width:0!important;"
                "max-width:100%!important;display:flex!important;flex-wrap:wrap}"
                "#primary-menu>li{float:none!important}}",
                1,
            )
        if domain == "apreal-nn.ru":
            source = source.replace(
                ".csf-actions{display:none!important}",
                '.csf-actions{display:none!important}'
                '.top-phone a[href="#phone-modal"]{display:block;margin-top:5px}'
                '.infographic input[name="phone-name"],'
                '.infographic input[name="phone-phone"]{width:240px!important;'
                'height:42px!important;padding:8px 10px!important;'
                'font-size:16px!important;box-sizing:border-box!important}'
                ".csf-modal{width:min(420px,calc(100vw - 28px))!important}",
                1,
            )
        if domain in ("apreal.spb.ru", "license39.ru", "apreal-nn.ru"):
            source = source.replace(
                ".csf-actions{display:none!important}",
                '.csf-actions{display:none!important}'
                '.csf-legacy-phone-form{display:grid!important;'
                'grid-template-columns:240px 240px max-content;'
                'width:max-content!important;max-width:100%;'
                'column-gap:22px;row-gap:0;align-items:end;'
                'position:relative!important;padding:0!important}'
                '.csf-legacy-phone-form>.inp1,.csf-legacy-phone-form>.inp2,'
                '.csf-legacy-phone-form>.inp3{position:static!important;left:auto!important;'
                'right:auto!important;top:auto!important;bottom:auto!important;'
                'width:auto!important;height:auto!important;margin:0!important;'
                'transform:none!important;float:none!important}'
                '.csf-legacy-phone-form>.inp1 label,.csf-legacy-phone-form>.inp2 label{'
                'display:block!important;margin:0 0 6px!important}'
                '.csf-legacy-phone-form>.inp1 input,.csf-legacy-phone-form>.inp2 input{'
                'display:block!important;width:240px!important;height:42px!important;'
                'box-sizing:border-box!important;margin:0!important}'
                '.csf-legacy-phone-form>.inp3 input{position:static!important;left:auto!important;'
                'right:auto!important;top:auto!important;bottom:auto!important;'
                'height:42px!important;margin:0!important;transform:none!important}'
                '.csf-legacy-phone-form>.csf-inline-result{grid-column:1/-1;grid-row:2;'
                'margin:4px 0 0!important;padding:4px 10px!important;line-height:1.2!important}'
                '@media(max-width:800px){.csf-legacy-phone-form{grid-template-columns:1fr!important;'
                'width:100%!important}'
                '.csf-legacy-phone-form>.inp1 input,.csf-legacy-phone-form>.inp2 input{'
                'width:100%!important}.csf-legacy-phone-form>.csf-inline-result{grid-column:1}}',
                1,
            )
        if domain == "apreal.spb.ru":
            source = source.replace(
                ".csf-actions{display:none!important}",
                '.csf-actions{display:none!important}'
                '.text3.info-texts{background:#fff!important;opacity:1!important;'
                'z-index:2!important}',
                1,
            )
        binding_items = ",".join(
            f"['{selector}','{kind}','{label}']"
            for selector, kind, label in site_bindings
        )
        bindings = (
            f"[{binding_items}].forEach(function(item){{"
            "document.querySelectorAll(item[0]).forEach(function(el){"
            "if(el.dataset.csfBound==='1')return;el.dataset.csfBound='1';"
            "if(el.tagName==='INPUT')el.value=item[2];else el.textContent=item[2];"
            "el.setAttribute('role','button');el.setAttribute('tabindex','0');"
            "function activate(event){event.preventDefault();event.stopImmediatePropagation();openModal(item[1]);}"
            "el.addEventListener('click',activate,true);el.addEventListener('keydown',function(event){"
            "if(event.key==='Enter'||event.key===' '){activate(event);}},true);});});"
        )
        source = source.replace(
            "document.querySelectorAll('a,button,[role=\"button\"],input[type=\"button\"]')",
            bindings
            + "document.querySelectorAll('a,button,[role=\"button\"],input[type=\"button\"]')",
            1,
        )
        source = source.replace(
            "if(el.closest('.csf-root')||el.closest('form'))return;",
            "if(el.dataset.csfBound==='1')return;if(el.closest('.csf-root')||el.closest('form'))return;",
            1,
        )
        if domain in ("nousro.ru", "ed-kgd.ru", "nousro-nn.ru"):
            source = source.replace(
                ".csf-actions{display:none!important}",
                '.csf-actions{display:none!important}'
                '.fixed-info__buttons{width:min(100%,420px)!important}'
                '.fixed-info__buttons .stacked-buttons{display:grid!important;'
                'grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;'
                'align-items:stretch!important}'
                '.fixed-info__buttons .stacked-buttons>.btn{width:100%!important;'
                'min-width:0!important;margin:0!important;padding:0 10px!important;'
                'white-space:normal!important;font-size:11px!important}'
                '.fixed-info__buttons .stacked-buttons>a:last-child,'
                '.fixed-info__buttons .stacked-buttons>noindex{grid-column:1/-1}'
                '.fixed-info__buttons .stacked-buttons>noindex>a{width:100%!important;'
                'margin:0!important}',
                1,
            )
            question_trigger = (
                "var callbackButton=document.querySelector('#mail-us');"
                "if(callbackButton&&callbackButton.parentElement&&!document.querySelector('.csf-template-question')){"
                "var questionButton=callbackButton.cloneNode(false);"
                "questionButton.removeAttribute('id');questionButton.removeAttribute('data-target');"
                "questionButton.classList.remove('modal-trigger');"
                "questionButton.classList.add('csf-template-question');"
                "questionButton.dataset.csfBound='1';questionButton.type='button';"
                "questionButton.textContent='ЗАДАТЬ ВОПРОС';"
                "questionButton.addEventListener('click',function(event){"
                "event.preventDefault();event.stopImmediatePropagation();openModal('question');},true);"
                "callbackButton.insertAdjacentElement('afterend',questionButton);}"
            )
            source = source.replace(
                "root.querySelectorAll('.csf-form')",
                question_trigger + "root.querySelectorAll('.csf-form')",
                1,
            )
    if domain in INLINE_STANDARD_ACTIONS:
        source = source.replace(
            "html.client-contact-modal-open body > jdiv",
            ".csf-actions.csf-actions-inline{position:static!important;"
            "left:auto!important;right:auto!important;bottom:auto!important;"
            "display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));"
            "width:min(100%,560px);max-width:none!important;margin:0 auto 18px!important;"
            "padding:0!important;justify-content:stretch!important}"
            ".csf-actions.csf-actions-inline .csf-action{width:100%;min-width:0;"
            "white-space:normal;text-align:center}"
            ".csf-actions.csf-actions-inline.csf-actions-narrow{"
            "grid-template-columns:1fr;width:100%;margin:8px 0 0!important}"
            "html.client-contact-modal-open body > jdiv",
            1,
        )
        placements = {
            "docp.ru": (
                "var actions=root.querySelector('.csf-actions');"
                "var desktopTarget=document.querySelector('.full-navigation');"
                "var mobileTarget=document.querySelector('main,.tm-main .tm-content,.tm-content');"
                "var isMobile=window.matchMedia('(max-width:767px)').matches;"
                "var target=isMobile?mobileTarget:desktopTarget;"
                "var legacy=desktopTarget?desktopTarget.querySelector('.uk-button-danger'):null;"
                "if(actions&&target){if(legacy)legacy.style.display='none';"
                "actions.classList.add('csf-actions-inline');"
                "if(!isMobile)actions.classList.add('csf-actions-narrow');"
                "target.insertBefore(actions,target.firstChild);}"
            ),
            "mchs78.ru": (
                "var actions=root.querySelector('.csf-actions');"
                "var target=document.querySelector('.callback-link');"
                "var legacy=target?target.querySelector('.callback-link__link'):null;"
                "if(actions&&target){if(legacy)legacy.style.display='none';"
                "actions.classList.add('csf-actions-inline','csf-actions-narrow');"
                "target.appendChild(actions);}"
            ),
            "apreal-volgograd.ru": (
                "var actions=root.querySelector('.csf-actions');"
                "var legacy=document.querySelector('.eModal-7');"
                "var target=legacy?legacy.closest('.textwidget'):null;"
                "if(actions&&target){if(legacy&&legacy.parentElement)"
                "legacy.parentElement.style.display='none';"
                "actions.classList.add('csf-actions-inline','csf-actions-narrow');"
                "target.appendChild(actions);}"
            ),
            "dpomuc.ru": (
                "var actions=root.querySelector('.csf-actions');"
                "var target=document.querySelector('.tm-main .tm-content');"
                "if(actions&&target){actions.classList.add('csf-actions-inline');"
                "target.insertBefore(actions,target.firstChild);}"
            ),
            "elecktro.ru": (
                "var actions=root.querySelector('.csf-actions');"
                "var target=document.querySelector('#tm-top-b .uk-container');"
                "if(actions&&target){actions.classList.add('csf-actions-inline');"
                "target.insertBefore(actions,target.firstChild);}"
            ),
        }
        source = source.replace(
            "root.querySelectorAll('.csf-form')",
            placements[domain] + "root.querySelectorAll('.csf-form')",
            1,
        )
    if domain in {"otxodi.ru", "mchs-spb.ru"}:
        source = source.replace(
            "html.client-contact-modal-open body > jdiv",
            ".csf-actions{display:none!important}"
            ".header-top .calc-button{cursor:pointer;transition:opacity .15s ease;"
            "text-decoration-thickness:1px;text-underline-offset:3px}"
            ".header-top .calc-button:hover{opacity:.72;text-decoration:underline}"
            ".header-top .calc-button:focus-visible{outline:2px solid currentColor;"
            "outline-offset:3px}"
            "@media(max-width:767px){.csf-actions.csf-actions-mobile{position:static!important;"
            "display:grid!important;grid-template-columns:1fr 1fr;gap:8px;max-width:none!important;"
            "margin:10px;padding:0 10px}}html.client-contact-modal-open body > jdiv",
            1,
        )
        header_bindings = (
            "[['.header-top .calc-button','question','ЗАДАТЬ ВОПРОС'],"
            "['.header-top .backform','callback','ЗАКАЗАТЬ ЗВОНОК']].forEach(function(item){"
            "var el=document.querySelector(item[0]);if(!el)return;el.textContent=item[2];"
            "el.setAttribute('role','button');el.setAttribute('tabindex','0');"
            "function activate(event){event.preventDefault();event.stopImmediatePropagation();openModal(item[1]);}"
            "el.addEventListener('click',activate,true);el.addEventListener('keydown',function(event){"
            "if(event.key==='Enter'||event.key===' '){activate(event);}},true);});"
            "var mobileActions=root.querySelector('.csf-actions');var mobileHeader=document.querySelector('header');"
            "if(mobileActions&&mobileHeader){mobileActions.classList.add('csf-actions-mobile');"
            "mobileHeader.insertAdjacentElement('afterend',mobileActions);}"
        )
        source = source.replace(
            "root.querySelectorAll('.csf-form')",
            header_bindings + "root.querySelectorAll('.csf-form')",
            1,
        )
    if domain == "muc-vrn.ru":
        source = source.replace(
            "html.client-contact-modal-open body > jdiv",
            ".csf-actions{display:none!important}"
            ".csf-muc-header-callback{box-sizing:border-box;display:inline-flex!important;align-items:center;justify-content:center;align-self:center;width:190px;height:40px;padding:0 18px;background:#ef476f;color:#fff!important;font:700 13px/1.2 Arial,sans-serif;text-decoration:none!important;box-shadow:0 3px 10px rgba(0,0,0,.18)}"
            ".mob-dop-btns{display:flex!important;flex:1;gap:8px;margin-left:16px}"
            ".csf-muc-mobile-callback,.csf-muc-mobile-question{display:inline-flex!important;align-items:center;justify-content:center;flex:1;min-width:0;height:40px;padding:0 8px;background:#ef476f!important;color:#fff!important;font:700 11px/1.15 Arial,sans-serif!important;text-align:center!important;text-decoration:none!important}"
            "@media(min-width:768px){.csf-muc-mobile-callback,.csf-muc-mobile-question{display:none!important}}"
            "html.client-contact-modal-open body > jdiv",
            1,
        )
        header_relocation = (
            "var headerCallback=document.querySelector('.fixed-line-right a');"
            "var header=document.querySelector('.logotype');"
            "var contacts=document.querySelector('.logotype__contactus');"
            "if(headerCallback&&header&&contacts){headerCallback.classList.add('csf-muc-header-callback');"
            "headerCallback.removeAttribute('target');headerCallback.setAttribute('href','#');"
            "header.insertBefore(headerCallback,contacts);}"
            "var mobileCallback=document.querySelector('.mob-dop-btns a');"
            "if(mobileCallback){mobileCallback.classList.add('csf-muc-mobile-callback');"
            "mobileCallback.removeAttribute('target');mobileCallback.setAttribute('href','#');"
            "var mobileQuestion=mobileCallback.cloneNode(false);"
            "mobileQuestion.classList.remove('csf-muc-mobile-callback');"
            "mobileQuestion.classList.add('csf-muc-mobile-question');"
            "mobileQuestion.dataset.csfBound='1';mobileQuestion.textContent='ЗАДАТЬ ВОПРОС';"
            "mobileQuestion.addEventListener('click',function(event){"
            "event.preventDefault();event.stopImmediatePropagation();openModal('question');},true);"
            "mobileCallback.insertAdjacentElement('afterend',mobileQuestion);}"
        )
        source = source.replace(
            "root.querySelectorAll('.csf-form')",
            header_relocation + "root.querySelectorAll('.csf-form')",
            1,
        )
    form_ids = LEGACY_CF7_FORMS.get(domain, ())
    if not form_ids:
        protection = ""
    else:
        ids = ", ".join(str(form_id) for form_id in form_ids)
        selectors = ",".join(
            f'[id^="wpcf7-f{form_id}-"]'
            for form_id in form_ids
        )
        protection = f"""function csf_block_legacy_cf7($spam)
{{
    if ($spam || !class_exists('WPCF7_ContactForm')) {{
        return $spam;
    }}
    $form = WPCF7_ContactForm::get_current();
    if (!$form || !in_array((int) $form->id(), array({ids}), true)) {{
        return $spam;
    }}
    return true;
}}
add_filter('wpcf7_spam', 'csf_block_legacy_cf7', PHP_INT_MAX);

function csf_hide_legacy_cf7()
{{
    echo '<style>{selectors}{{display:none!important}}</style>';
}}
add_action('wp_head', 'csf_hide_legacy_cf7', 1000);"""
    return source.replace("__LEGACY_CF7_PROTECTION__", protection)


def render_static_handler(domain: str, recipient: str) -> str:
    template = (
        MEDTEX39_HANDLER_TEMPLATE
        if domain == "medtex39.ru"
        else STATIC_HANDLER_TEMPLATE
    )
    return replace_contract(template, domain, recipient)


def render_static_script(domain: str = "") -> str:
    source = replace_contract(STATIC_SCRIPT_TEMPLATE)
    if domain == "lfsb.ru":
        source = source.replace(
            "var callbackLabels=",
            "var legacyCallbackAnchor=null;var callbackLabels=",
            1,
        )
        source = source.replace(
            "if(!kind)return;if(el.tagName===",
            "if(!kind)return;if(kind==='callback'&&!legacyCallbackAnchor)legacyCallbackAnchor=el;if(el.tagName===",
            1,
        )
        source = source.replace(
            "var sidebar=document.querySelector('#leblok');if(sidebar&&actions){actions.classList.add('csf-actions-sidebar');sidebar.insertBefore(actions,sidebar.firstChild);}",
            "var sidebar=document.querySelector('#leblok,#le5');var fallbackAnchor=null;if(!sidebar&&legacyCallbackAnchor){sidebar=legacyCallbackAnchor.parentElement;fallbackAnchor=legacyCallbackAnchor;}if(sidebar&&actions){actions.classList.add('csf-actions-sidebar');sidebar.insertBefore(actions,fallbackAnchor||sidebar.firstChild);}if(legacyCallbackAnchor)legacyCallbackAnchor.style.display='none';",
            1,
        )
    if domain == "shopap.ru":
        source = source.replace(
            ".csf-actions.csf-actions-sidebar{",
            ".csf-actions.csf-actions-shop{position:static;right:auto;bottom:auto;display:grid;grid-template-columns:1fr 1fr;gap:8px;width:100%;max-width:none;margin:0 0 18px;padding:0}"
            ".csf-actions.csf-actions-sidebar{",
            1,
        )
        source = source.replace(
            "var sidebar=document.querySelector('#leblok');if(sidebar&&actions){actions.classList.add('csf-actions-sidebar');sidebar.insertBefore(actions,sidebar.firstChild);}",
            "var shopContent=document.querySelector('#content');if(shopContent&&actions){actions.classList.add('csf-actions-shop');shopContent.insertBefore(actions,shopContent.firstChild);}",
            1,
        )
    if domain == "medtex39.ru":
        source = source.replace(
            '<input type="hidden" name="page">',
            '<input type="hidden" name="page">'
            '<input type="hidden" name="form_token">',
        )
        source = source.replace(
            ".csf-actions{position:fixed;right:96px;bottom:16px;"
            "z-index:2147483600;display:flex;gap:8px;flex-wrap:wrap;"
            "justify-content:flex-end;max-width:calc(100vw - 112px)}",
            ".csf-actions{position:static;display:grid;gap:8px;"
            "max-width:none;margin:0 0 20px}",
            1,
        )
        source = source.replace(
            "document.body.appendChild(root);",
            "var actionHost=document.querySelector('.navigation-left.full-navigation');"
            "if(actionHost)actionHost.insertAdjacentElement('afterend',root);"
            "else document.body.appendChild(root);",
            1,
        )
        source = source.replace(
            "var overlay=root.querySelector('.csf-overlay');var actions=",
            "var overlay=root.querySelector('.csf-overlay');"
            "function loadChallenge(form){var token=form.querySelector('[name=\"form_token\"]');"
            "var submit=form.querySelector('.csf-submit');var result=form.querySelector('.csf-result');"
            "token.value='';submit.disabled=true;"
            "return fetch('/client-standard-mail.php?challenge=1',"
            "{credentials:'same-origin',cache:'no-store'}).then(function(response){"
            "return response.json().then(function(payload){return {ok:response.ok,payload:payload};});"
            "}).then(function(outcome){if(!outcome.ok||!outcome.payload.token)"
            "throw new Error('Не удалось подготовить форму.');token.value=outcome.payload.token;"
            "}).catch(function(error){result.textContent=error.message||"
            "'Не удалось подготовить форму.';result.classList.add('is-visible','is-error');"
            "}).finally(function(){submit.disabled=false;});}var actions=",
            1,
        )
        source = source.replace(
            "document.documentElement.style.overflow='hidden';",
            "loadChallenge(modal.querySelector('.csf-form'));"
            "document.documentElement.style.overflow='hidden';",
            1,
        )
        source = source.replace(
            "var result=form.querySelector('.csf-result');"
            "form.querySelector('[name=\"page\"]').value=window.location.href;",
            "var result=form.querySelector('.csf-result');"
            "if(!form.querySelector('[name=\"form_token\"]').value){"
            "result.textContent='Подождите, форма загружается.';"
            "result.className='csf-result is-visible is-error';loadChallenge(form);return;}"
            "form.querySelector('[name=\"page\"]').value=window.location.href;",
            1,
        )
        source = source.replace(
            "form.reset();",
            "form.reset();loadChallenge(form);",
            1,
        )
    return "".join(
        char if ord(char) < 128 else f"\\u{ord(char):04x}"
        for char in source
    )


def build_domain(
    output_root: Path,
    domain: str,
    recipient: str,
    platform: str,
) -> None:
    if domain in EXCLUDED:
        raise ValueError(f"Excluded by client request: {domain}")
    target = output_root / domain
    target.mkdir(parents=True, exist_ok=True)
    if platform == "wordpress":
        (target / "client-standard-forms.php").write_text(
            render_wordpress_plugin(domain, recipient),
            encoding="utf-8",
        )
    elif platform == "static":
        (target / "client-standard-mail.php").write_text(
            render_static_handler(domain, recipient),
            encoding="utf-8",
        )
        (target / "client-standard-forms.js").write_text(
            render_static_script(domain),
            encoding="utf-8",
        )
    else:
        raise ValueError(f"Unknown platform: {platform}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("generated"),
    )
    args = parser.parse_args()
    for domain, recipient in WORDPRESS_SITES.items():
        build_domain(args.output, domain, recipient, "wordpress")
    for domain, recipient in STATIC_SITES.items():
        build_domain(args.output, domain, recipient, "static")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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

WORDPRESS_SITES = {
    "docp.ru": "info@docp.ru",
    "elecktro.ru": "info@elecktro.ru",
    "medlic.spb.ru": "info@medlic.spb.ru",
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
    html.client-contact-modal-open body > jdiv{display:none!important}.csf-root,.csf-root *{box-sizing:border-box}.csf-actions{position:fixed;right:96px;bottom:16px;z-index:2147483600;display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:calc(100vw - 112px)}.csf-action,.csf-submit{border:0;border-radius:4px;background:#c62828;color:#fff;padding:12px 16px;font:700 14px/1.2 Arial,sans-serif;letter-spacing:0;cursor:pointer;box-shadow:0 3px 12px rgba(0,0,0,.22)}.csf-action-secondary{background:#263238}.csf-overlay{position:fixed;inset:0;z-index:2147483601;background:rgba(0,0,0,.62)}.csf-modal{position:fixed;z-index:2147483602;left:50%;top:50%;transform:translate(-50%,-50%);width:min(520px,calc(100vw - 28px));max-height:calc(100vh - 28px);overflow:auto;background:#fff;color:#222;padding:28px;border-radius:6px;box-shadow:0 12px 50px rgba(0,0,0,.4);font-family:Arial,sans-serif}.csf-overlay[hidden],.csf-modal[hidden]{display:none!important}.csf-modal h2{margin:0 42px 22px 0;font:700 24px/1.2 Arial,sans-serif;letter-spacing:0;color:#222}.csf-close{position:absolute;right:12px;top:8px;width:38px;height:38px;border:0;background:transparent;color:#111;font:700 34px/34px Arial,sans-serif;cursor:pointer}.csf-form{display:grid;gap:14px}.csf-form label{display:grid;gap:6px;font:600 14px/1.3 Arial,sans-serif;color:#222}.csf-form input,.csf-form textarea{width:100%;border:1px solid #999;border-radius:3px;background:#fff;color:#111;padding:11px 12px;font:400 16px/1.3 Arial,sans-serif;letter-spacing:0}.csf-form textarea{resize:vertical}.csf-consent{margin:0;font:400 12px/1.45 Arial,sans-serif;color:#444}.csf-consent a{color:#0b57d0;text-decoration:underline}.csf-optional{font-weight:400;color:#666}.csf-result{display:none;margin:0;padding:10px;border:1px solid #2e7d32;color:#1b5e20;font:600 14px/1.4 Arial,sans-serif}.csf-result.is-visible{display:block}.csf-result.is-error{border-color:#c62828;color:#b71c1c}.csf-honeypot{position:absolute!important;left:-10000px!important;width:1px!important;height:1px!important;opacity:0!important}.csf-submit[disabled]{opacity:.65;cursor:wait}@media(max-width:560px){.csf-actions{left:10px;right:72px;bottom:10px;display:grid;grid-template-columns:1fr 1fr;max-width:none}.csf-action{padding:11px 8px;font-size:12px}.csf-modal{padding:22px 18px}.csf-modal h2{font-size:20px}}
    </style>
    <script>
    document.addEventListener('DOMContentLoaded',function(){var root=document.querySelector('.csf-root');if(!root)return;if(root.parentNode!==document.body)document.body.appendChild(root);var overlay=root.querySelector('.csf-overlay');var modals=root.querySelectorAll('.csf-modal');function closeAll(){overlay.hidden=true;modals.forEach(function(modal){modal.hidden=true;});document.documentElement.style.overflow='';document.documentElement.classList.remove('client-contact-modal-open');}function openModal(kind){closeAll();var modal=root.querySelector('[data-modal="'+kind+'"]');if(!modal)return;overlay.hidden=false;modal.hidden=false;document.documentElement.style.overflow='hidden';document.documentElement.classList.add('client-contact-modal-open');var field=modal.querySelector('input:not([type="hidden"]):not(.csf-honeypot)');if(field)field.focus();}root.querySelectorAll('.csf-open-callback').forEach(function(el){el.addEventListener('click',function(){openModal('callback');});});root.querySelectorAll('.csf-open-question').forEach(function(el){el.addEventListener('click',function(){openModal('question');});});root.querySelectorAll('.csf-close').forEach(function(el){el.addEventListener('click',closeAll);});overlay.addEventListener('click',closeAll);document.addEventListener('keydown',function(event){if(event.key==='Escape')closeAll();});var callbackLabels=['заказать звонок','обратный звонок','перезвонить','бесплатная консультация','получить бесплатную консультацию','оставить заявку'];var questionLabels=['задать вопрос','расчет стоимости','расчёт стоимости','узнать цену'];document.querySelectorAll('a,button,[role="button"],input[type="button"]').forEach(function(el){if(el.closest('.csf-root')||el.closest('form'))return;var raw=el.tagName==='INPUT'?el.value:el.textContent;var label=(raw||'').replace(/\s+/g,' ').trim().toLowerCase();if(!label||label.length>90)return;var kind='';if(questionLabels.some(function(x){return label.indexOf(x)!==-1;}))kind='question';else if(callbackLabels.some(function(x){return label.indexOf(x)!==-1;}))kind='callback';if(!kind)return;if(el.tagName==='INPUT')el.value=kind==='callback'?'ЗАКАЗАТЬ ЗВОНОК':'ЗАДАТЬ ВОПРОС';else el.textContent=kind==='callback'?'ЗАКАЗАТЬ ЗВОНОК':'ЗАДАТЬ ВОПРОС';el.addEventListener('click',function(event){event.preventDefault();event.stopImmediatePropagation();openModal(kind);},true);});root.querySelectorAll('.csf-form').forEach(function(form){form.addEventListener('submit',function(event){event.preventDefault();var submit=form.querySelector('.csf-submit');var result=form.querySelector('.csf-result');var page=form.querySelector('[name="page"]');page.value=window.location.href;result.className='csf-result';result.textContent='';submit.disabled=true;fetch(root.dataset.endpoint,{method:'POST',body:new FormData(form),credentials:'same-origin'}).then(function(response){return response.json().then(function(payload){return {ok:response.ok,payload:payload};});}).then(function(outcome){var payload=outcome.payload;var message=payload&&payload.data&&payload.data.message?payload.data.message:'Не удалось отправить сообщение.';if(!outcome.ok||!payload.success)throw new Error(message);result.textContent=message;result.classList.add('is-visible');form.reset();}).catch(function(error){result.textContent=error.message||'Не удалось отправить сообщение.';result.classList.add('is-visible','is-error');}).finally(function(){submit.disabled=false;});});});});
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
$sent = mail(CSF_RECIPIENT, $subject, $message, implode("\r\n", $headers));
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
    if domain == "otxodi.ru":
        source = source.replace(
            "html.client-contact-modal-open body > jdiv",
            ".csf-actions{display:none!important}@media(max-width:767px){.csf-actions.csf-actions-mobile{position:static!important;display:grid!important;grid-template-columns:1fr 1fr;gap:8px;max-width:none!important;margin:10px;padding:0 10px}}html.client-contact-modal-open body > jdiv",
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
    return replace_contract(STATIC_HANDLER_TEMPLATE, domain, recipient)


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

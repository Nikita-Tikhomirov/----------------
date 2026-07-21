<?php

require_once __DIR__ . '/wp-load.php';

$request_method = isset($_SERVER['REQUEST_METHOD']) ? $_SERVER['REQUEST_METHOD'] : '';
if ('POST' !== $request_method) {
    wp_send_json_error(array('message' => 'Метод запроса не поддерживается.'), 405);
}

if (!empty($_POST['company'])) {
    wp_send_json_success();
}

$name_value = isset($_POST['phone-name']) ? $_POST['phone-name'] : '';
$phone_value = isset($_POST['phone-phone']) ? $_POST['phone-phone'] : '';
$name = sanitize_text_field(wp_unslash($name_value));
$phone = sanitize_text_field(wp_unslash($phone_value));

if ('' === $phone) {
    wp_send_json_error(array('message' => 'Укажите номер телефона.'), 422);
}

$ip_value = isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : 'unknown';
$ip = sanitize_text_field(wp_unslash($ip_value));
$rate_key = 'apreal_callback_' . md5($ip);
if (get_transient($rate_key)) {
    wp_send_json_error(array('message' => 'Заявка уже отправлена. Пожалуйста, подождите немного.'), 429);
}

$subject = 'Заказ обратного звонка с сайта apreal.ru';
$body = "Имя: {$name}\nТелефон: {$phone}\nСтраница: " . home_url('/');
$headers = array('From: ГК АП-Риал <info@apreal.ru>');

if (!wp_mail('info@apreal.ru', $subject, $body, $headers)) {
    wp_send_json_error(array('message' => 'Не удалось отправить сообщение. Позвоните нам по телефону.'), 500);
}

set_transient($rate_key, 1, MINUTE_IN_SECONDS);
wp_send_json_success();

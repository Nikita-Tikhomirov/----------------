<?php
ini_set('display_errors', '0');
error_reporting(E_ALL);
header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store');

function respond($success, $message) {
    echo wp_json_encode(['success' => $success, 'message' => $message]);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit;
}

define('WP_USE_THEMES', false);
require_once $_SERVER['DOCUMENT_ROOT'] . '/wp-load.php';

const APREAL_FORM_SENDER = 'wordpress@mca24.ru';

function apreal_form_set_envelope_sender($phpmailer) {
    $phpmailer->Sender = $phpmailer->From;
}

if (trim((string) (isset($_POST['captcha']) ? $_POST['captcha'] : '')) !== '5') {
    respond(false, 'Неверно введено контрольное число.');
}

$form_id = sanitize_key(isset($_POST['formid']) ? $_POST['formid'] : '');
$page = esc_html(wp_unslash(isset($_POST['page']) ? $_POST['page'] : ''));
$headers = [
    'Content-Type: text/html; charset=UTF-8',
    'From: mca24.ru <' . APREAL_FORM_SENDER . '>',
    'Reply-To: ' . APREAL_FORM_SENDER,
];

if ($form_id === 'callback') {
    $name = sanitize_text_field(wp_unslash(isset($_POST['name']) ? $_POST['name'] : ''));
    $phone = esc_html(wp_unslash(isset($_POST['phone']) ? $_POST['phone'] : ''));
    if ($phone === '') {
        respond(false, 'Введите телефон.');
    }
    $subject = 'Заказать звонок';
    $message = "<p><strong>Имя:</strong> {$name}</p><p><strong>Телефон:</strong> {$phone}</p><p><strong>Страница:</strong> {$page}</p>";
} elseif ($form_id === 'question') {
    $name = sanitize_text_field(wp_unslash(isset($_POST['name']) ? $_POST['name'] : ''));
    $phone = sanitize_text_field(wp_unslash(isset($_POST['phone']) ? $_POST['phone'] : ''));
    $comment = esc_html(wp_unslash(isset($_POST['coment']) ? $_POST['coment'] : ''));
    if ($phone === '') {
        respond(false, 'Введите телефон.');
    }
    $subject = 'Задать вопрос';
    $message = "<p><strong>Имя:</strong> {$name}</p><p><strong>Телефон:</strong> {$phone}</p><p><strong>Вопрос:</strong> {$comment}</p><p><strong>Страница:</strong> {$page}</p>";
} else {
    respond(false, 'Неизвестная форма.');
}

add_action('phpmailer_init', 'apreal_form_set_envelope_sender', 999);
$sent = wp_mail('info@mca24.ru', $subject, $message, $headers);
remove_action('phpmailer_init', 'apreal_form_set_envelope_sender', 999);
respond($sent, $sent ? 'Спасибо за Ваше сообщение. Оно успешно отправлено' : 'Не удалось отправить сообщение. Попробуйте еще раз.');

<?php
ini_set('display_errors', '0');
error_reporting(E_ALL);
header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store');

function respond($success, $message) {
    echo json_encode(['success' => $success, 'message' => $message], JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit;
}

if (trim((string) (isset($_POST['captcha']) ? $_POST['captcha'] : '')) !== '5') {
    respond(false, 'Неверно введено контрольное число.');
}

$form_id = preg_replace('/[^a-z_-]/', '', (string) (isset($_POST['formid']) ? $_POST['formid'] : ''));
$page = htmlspecialchars(trim((string) (isset($_POST['page']) ? $_POST['page'] : '')), ENT_QUOTES, 'UTF-8');
$headers = [
    'MIME-Version: 1.0',
    'Content-Type: text/html; charset=UTF-8',
    'From: fsa-lab.ru <wordpress@fsa-lab.ru>',
];

if ($form_id === 'callback') {
    $name = htmlspecialchars(trim((string) (isset($_POST['name']) ? $_POST['name'] : '')), ENT_QUOTES, 'UTF-8');
    $phone = htmlspecialchars(trim((string) (isset($_POST['phone']) ? $_POST['phone'] : '')), ENT_QUOTES, 'UTF-8');
    if ($phone === '') {
        respond(false, 'Введите телефон.');
    }
    $subject = 'Заказать звонок';
    $message = "<p><strong>Имя:</strong> {$name}</p><p><strong>Телефон:</strong> {$phone}</p><p><strong>Страница:</strong> {$page}</p>";
} elseif ($form_id === 'question') {
    $name = htmlspecialchars(trim((string) (isset($_POST['name']) ? $_POST['name'] : '')), ENT_QUOTES, 'UTF-8');
    $phone = htmlspecialchars(trim((string) (isset($_POST['phone']) ? $_POST['phone'] : '')), ENT_QUOTES, 'UTF-8');
    $comment = htmlspecialchars(trim((string) (isset($_POST['coment']) ? $_POST['coment'] : '')), ENT_QUOTES, 'UTF-8');
    if ($phone === '') {
        respond(false, 'Введите телефон.');
    }
    $subject = 'Задать вопрос';
    $message = "<p><strong>Имя:</strong> {$name}</p><p><strong>Телефон:</strong> {$phone}</p><p><strong>Вопрос:</strong> {$comment}</p><p><strong>Страница:</strong> {$page}</p>";
} else {
    respond(false, 'Неизвестная форма.');
}

$encoded_subject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
$sent = mail('info@fsa-lab.ru', $encoded_subject, $message, implode("\r\n", $headers));
respond($sent, $sent ? 'Спасибо за Ваше сообщение. Оно успешно отправлено' : 'Не удалось отправить сообщение. Попробуйте еще раз.');

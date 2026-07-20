<?php
ini_set('display_errors', '0');
error_reporting(E_ALL);
header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store');

const CSF_DOMAIN = 'fste.ru';
const CSF_RECIPIENT = 'info@fste.ru';
const CSF_SENDER = 'wordpress@fste.ru';
const CSF_SUCCESS = 'Спасибо за Ваше сообщение. Оно успешно отправлено';

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
    $phone = isset($_POST['phone']) ? trim(strip_tags((string) $_POST['phone'])) : '';
    if ($phone === '') {
        respond(false, 'Введите телефон.', 400);
    }
    $subject = 'ЗАКАЗАТЬ ЗВОНОК — ' . CSF_DOMAIN;
    $message = '<p><strong>Телефон:</strong> ' . htmlspecialchars($phone, ENT_QUOTES, 'UTF-8') . '</p>';
} elseif ($kind === 'question') {
    $email = isset($_POST['email']) ? filter_var((string) $_POST['email'], FILTER_VALIDATE_EMAIL) : false;
    $question = isset($_POST['question']) ? trim(strip_tags((string) $_POST['question'])) : '';
    if (!$email) {
        respond(false, 'Введите корректный email.', 400);
    }
    $subject = 'ЗАДАТЬ ВОПРОС — ' . CSF_DOMAIN;
    $message = '<p><strong>Email:</strong> ' . htmlspecialchars($email, ENT_QUOTES, 'UTF-8') . '</p>';
    if ($question !== '') {
        $message .= '<p><strong>Вопрос:</strong><br>' . nl2br(htmlspecialchars($question, ENT_QUOTES, 'UTF-8')) . '</p>';
    }
    $headers[] = 'Reply-To: ' . $email;
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

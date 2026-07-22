<?php
ini_set('display_errors', '0');
error_reporting(E_ALL);
header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

const CSF_DOMAIN = 'medtex39.ru';
const CSF_RECIPIENT = 'info@medtex39.ru';
const CSF_SENDER = 'wordpress@medtex39.ru';
const CSF_SUCCESS = 'Спасибо за Ваше сообщение. Оно успешно отправлено';
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
);

if ($kind === 'callback') {
    $phone = clean_value('phone');
    $phone_digits = preg_replace('/\D+/', '', $phone);
    if (strlen($phone_digits) < 7 || strlen($phone_digits) > 18) {
        respond(false, 'Введите корректный телефон.', 400);
    }
    $subject = 'ЗАКАЗАТЬ ЗВОНОК — ' . CSF_DOMAIN;
    $message = '<p><strong>Телефон:</strong> '
        . htmlspecialchars($phone, ENT_QUOTES, 'UTF-8') . '</p>';
} elseif ($kind === 'question') {
    $email = isset($_POST['email'])
        ? filter_var((string) $_POST['email'], FILTER_VALIDATE_EMAIL)
        : false;
    $question = clean_value('question');
    if (!$email) {
        respond(false, 'Введите корректный email.', 400);
    }
    $subject = 'ЗАДАТЬ ВОПРОС — ' . CSF_DOMAIN;
    $message = '<p><strong>Email:</strong> '
        . htmlspecialchars($email, ENT_QUOTES, 'UTF-8') . '</p>';
    if ($question !== '') {
        $message .= '<p><strong>Вопрос:</strong><br>'
            . nl2br(htmlspecialchars($question, ENT_QUOTES, 'UTF-8')) . '</p>';
    }
    $headers[] = 'Reply-To: ' . $email;
} else {
    respond(false, 'Неизвестная форма.', 400);
}

$message .= '<p><strong>Страница:</strong> '
    . htmlspecialchars($page, ENT_QUOTES, 'UTF-8') . '</p>';
$sent = mail(CSF_RECIPIENT, $subject, $message, implode("\r\n", $headers));
if ($sent) {
    @touch($rate_file);
}
respond(
    $sent,
    $sent ? CSF_SUCCESS : 'Не удалось отправить сообщение. Попробуйте еще раз.',
    $sent ? 200 : 500
);

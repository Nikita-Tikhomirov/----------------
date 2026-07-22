<?php
header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store');
http_response_code(410);

echo json_encode(array(
    'mailSent' => 0,
    'into' => '#wpcf7-f3260-o1',
    'message' => 'Эта форма обновлена. Используйте кнопки связи на сайте.',
    'invalids' => array(),
    'replacement' => '/client-standard-mail.php',
), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

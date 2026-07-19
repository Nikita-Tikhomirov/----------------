<?php

$form_id = 5;
$form = <<<'FORM'
<label> Ваше имя
    [text your-name] </label>

<label> Ваш телефон
    [tel* tel-639] </label>
[quiz quiz-500 "Введите цифрами: Пятьдесят пять|55"]
[submit "Отправить"]
FORM;

update_post_meta($form_id, '_form', $form);

$mail = get_post_meta($form_id, '_mail', true);
$mail['subject'] = 'Заявка с сайта elecktro.ru';
$mail['sender'] = 'elecktro.ru <wordpress@elecktro.ru>';
$mail['body'] = <<<'MAIL'
Заявка на регистрацию электролаборатории

Имя: [your-name]
Телефон: [tel-639]

Пожалуйста свяжитесь с клиентом в ближайшее время.
--
Это сообщение отправлено с сайта https://elecktro.ru
MAIL;
$mail['additional_headers'] = '';
update_post_meta($form_id, '_mail', $mail);

wp_update_post([
    'ID' => $form_id,
    'post_title' => 'ЗАКАЗАТЬ ЗВОНОК',
]);

global $wpdb;
$wpdb->update(
    $wpdb->prefix . 'em_modals',
    [
        'title' => 'ЗАКАЗАТЬ ЗВОНОК',
        'content' => '[contact-form-7 id="5" title="ЗАКАЗАТЬ ЗВОНОК"]',
    ],
    ['id' => 1],
    ['%s', '%s'],
    ['%d']
);

$widgets = get_option('widget_custom_html', []);
foreach ($widgets as &$widget) {
    if (!is_array($widget)) {
        continue;
    }

    if (isset($widget['title']) && $widget['title'] === 'ЗАКАЗАТЬ') {
        $widget['title'] = 'ЗАКАЗАТЬ ЗВОНОК';
    }

    if (isset($widget['content'])) {
        $widget['content'] = str_replace(
            ['>Оставить заявку<', '>ЗАКАЗАТЬ<'],
            ['>ЗАКАЗАТЬ ЗВОНОК<', '>ЗАКАЗАТЬ ЗВОНОК<'],
            $widget['content']
        );
    }
}
unset($widget);
update_option('widget_custom_html', $widgets);

$widgetkit_table = $wpdb->prefix . 'widgetkit';
$widgetkit_rows = $wpdb->get_results(
    "SELECT id, data FROM {$widgetkit_table}",
    ARRAY_A
);

$replace_cta = static function (&$value) use (&$replace_cta) {
    if (is_array($value)) {
        foreach ($value as &$child) {
            $replace_cta($child);
        }
        unset($child);
        return;
    }

    if (is_string($value)) {
        $value = str_replace(
            ['>Оставить заявку<', '>ЗАКАЗАТЬ<'],
            ['>ЗАКАЗАТЬ ЗВОНОК<', '>ЗАКАЗАТЬ ЗВОНОК<'],
            $value
        );
    }
};

foreach ($widgetkit_rows as $row) {
    $data = json_decode($row['data'], true);
    if (!is_array($data)) {
        continue;
    }

    $replace_cta($data);
    $wpdb->update(
        $widgetkit_table,
        ['data' => wp_json_encode($data, JSON_UNESCAPED_UNICODE)],
        ['id' => (int) $row['id']],
        ['%s'],
        ['%d']
    );
}

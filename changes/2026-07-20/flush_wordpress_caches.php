<?php

$root = isset($argv[1]) ? rtrim($argv[1], '/') : '';
if ($root === '') {
    fwrite(STDERR, "Usage: flush_wordpress_caches.php ROOT\n");
    exit(2);
}

$loader = $root . '/wp-load.php';
if (!is_file($loader)) {
    echo json_encode(array('root' => $root, 'error' => 'wp-load.php missing')) . "\n";
    exit(1);
}

$_SERVER['HTTP_HOST'] = basename(dirname($root));
$_SERVER['REQUEST_METHOD'] = 'GET';
$_SERVER['REQUEST_URI'] = '/';
define('WP_USE_THEMES', false);
require_once $loader;

$actions = array();
if (function_exists('wp_cache_flush')) {
    wp_cache_flush();
    $actions[] = 'wp_cache_flush';
}
if (function_exists('w3tc_flush_all')) {
    w3tc_flush_all();
    $actions[] = 'w3tc_flush_all';
}
if (function_exists('wp_cache_clear_cache')) {
    wp_cache_clear_cache();
    $actions[] = 'wp_cache_clear_cache';
}
if (function_exists('rocket_clean_domain')) {
    rocket_clean_domain();
    $actions[] = 'rocket_clean_domain';
}
if (function_exists('wpfc_clear_all_cache')) {
    wpfc_clear_all_cache(true);
    $actions[] = 'wpfc_clear_all_cache';
}
echo json_encode(
    array('root' => $root, 'actions' => $actions),
    JSON_UNESCAPED_UNICODE
) . "\n";

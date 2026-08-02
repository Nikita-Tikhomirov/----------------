<?php
/**
 * Plugin Name: Client Form Envelope Sender
 * Description: Keeps Contact Form 7 From, Reply-To and SMTP envelope sender aligned.
 */

if (!defined('ABSPATH')) {
    exit;
}

const APREAL_FORM_ENVELOPE_SENDER = 'wordpress@nousro-spb.ru';

function apreal_form_align_envelope_sender($phpmailer)
{
    $phpmailer->Sender = $phpmailer->From;
}
add_action('phpmailer_init', 'apreal_form_align_envelope_sender', 999);

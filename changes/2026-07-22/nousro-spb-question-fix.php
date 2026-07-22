<?php
/**
 * Plugin Name: Nousro SPB Question Form Fix
 * Description: Keeps the question-form result visible and away from JivoSite.
 */

if (!defined('ABSPATH')) {
    exit;
}

function nousro_spb_render_question_form_fix()
{
    if (is_admin()) {
        return;
    }
    ?>
    <style>
    html.nousro-spb-question-open body > jdiv{display:none!important}
    #modal1{overflow-y:auto!important;max-height:calc(100vh - 28px)!important;top:14px!important}
    #modal1 .modal-content{padding-top:24px!important}
    #modal1 .form-modal-close{position:sticky!important;top:0!important;float:right!important;z-index:5!important;margin:0!important}
    #modal1 .modal-title{padding-right:58px!important}
    #modal1 .wpcf7-response-output{position:relative!important;z-index:2;margin:12px 0!important;padding:10px 12px!important;border:1px solid #2e7d32!important;background:#fff!important;color:#1b5e20!important;font:600 14px/1.4 Arial,sans-serif!important}
    #modal1 .wpcf7-response-output[aria-hidden="true"]:empty{display:none!important}
    #modal1 .wpcf7-form.failed .wpcf7-response-output,#modal1 .wpcf7-form.invalid .wpcf7-response-output{border-color:#c62828!important;color:#b71c1c!important}
    </style>
    <script>
    document.addEventListener('DOMContentLoaded',function(){
        var modal=document.getElementById('modal1');
        if(!modal)return;
        var form=modal.querySelector('.wpcf7-form');
        var response=form&&form.querySelector('.wpcf7-response-output');
        var submit=form&&form.querySelector('.wpcf7-submit');
        if(response&&submit&&submit.parentNode){
            submit.parentNode.insertBefore(response, submit);
        }
        function syncModalState(){
            document.documentElement.classList.toggle(
                'nousro-spb-question-open',
                modal.classList.contains('open')
            );
        }
        new MutationObserver(syncModalState).observe(modal,{attributes:true,attributeFilter:['class']});
        syncModalState();
        function revealResult(event){
            if(!event.detail||String(event.detail.contactFormId)!=='2005')return;
            syncModalState();
            if(response){
                setTimeout(function(){
                    modal.scrollTop=0;
                },100);
            }
        }
        document.addEventListener('wpcf7mailsent',revealResult);
        document.addEventListener('wpcf7mailfailed',revealResult);
        document.addEventListener('wpcf7invalid',revealResult);
    });
    </script>
    <?php
}
add_action('wp_footer', 'nousro_spb_render_question_form_fix', 1001);

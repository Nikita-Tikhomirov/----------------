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
    #modal1,#modal2{overflow-y:auto!important;overflow-x:hidden!important;max-height:calc(100vh - 28px)!important;top:14px!important}
    #modal1 .modal-content,#modal2 .modal-content{padding-top:24px!important}
    #modal1 .form-modal-close,#modal2 .form-modal-close{position:sticky!important;top:0!important;float:right!important;z-index:5!important;margin:0!important;font-size:0!important;line-height:0!important}
    #modal1 .form-modal-close::before,#modal1 .form-modal-close::after,#modal2 .form-modal-close::before,#modal2 .form-modal-close::after{content:""!important;position:absolute!important;left:50%!important;top:50%!important;width:20px!important;height:2px!important;background:#fff!important;transform-origin:center!important}
    #modal1 .form-modal-close::before,#modal2 .form-modal-close::before{transform:translate(-50%,-50%) rotate(45deg)!important}
    #modal1 .form-modal-close::after,#modal2 .form-modal-close::after{transform:translate(-50%,-50%) rotate(-45deg)!important}
    #modal1 .modal-title,#modal2 .modal-title{padding-right:58px!important}
    #modal1 .wpcf7-response-output{position:relative!important;z-index:2;margin:12px 0!important;padding:10px 12px!important;border:1px solid #2e7d32!important;background:#fff!important;color:#1b5e20!important;font:600 14px/1.4 Arial,sans-serif!important}
    #modal1 .wpcf7-response-output[aria-hidden="true"]:empty{display:none!important}
    #modal1 .wpcf7-form.failed .wpcf7-response-output,#modal1 .wpcf7-form.invalid .wpcf7-response-output{border-color:#c62828!important;color:#b71c1c!important}
    @media(max-width:600px){.mob-top{display:flex!important;align-items:center;gap:6px}.mob-top .nousro-spb-mobile-actions{display:grid;grid-template-columns:1fr 1fr;gap:6px;width:190px;margin-left:auto}.mob-top .nousro-spb-mobile-actions .btn{display:block!important;width:100%!important;height:36px!important;min-width:0!important;margin:0!important;padding:0 6px!important;font-size:11px!important;line-height:36px!important;letter-spacing:0!important;white-space:nowrap}.mob-top #feather-menu{flex:0 0 24px;margin:0!important}#modal1 .modal-title,#modal2 .modal-title{font-size:28px!important;line-height:1.2!important;padding-right:48px!important}}
    </style>
    <script>
    document.addEventListener('DOMContentLoaded',function(){
        var modal=document.getElementById('modal1');
        var callbackModal=document.getElementById('modal2');
        if(!modal)return;
        var mobileRow=document.querySelector('.fixed-info__item.mob-top');
        var mobileCallback=mobileRow&&mobileRow.querySelector('a[href="#modal2"]');
        var mobileMenu=mobileRow&&mobileRow.querySelector('#feather-menu');
        if(mobileRow&&mobileCallback&&mobileMenu&&!mobileRow.querySelector('.nousro-spb-mobile-actions')){
            var mobileActions=document.createElement('div');
            var mobileQuestion=document.createElement('button');
            mobileActions.className='nousro-spb-mobile-actions hide-on-med-and-up';
            mobileQuestion.type='button';
            mobileQuestion.className='btn red darken-2 waves-effect waves-light nousro-spb-mobile-question';
            mobileQuestion.textContent='ВОПРОС';
            mobileCallback.textContent='ЗВОНОК';
            mobileRow.insertBefore(mobileActions,mobileMenu);
            mobileActions.appendChild(mobileQuestion);
            mobileActions.appendChild(mobileCallback);
            mobileQuestion.addEventListener('click',function(){
                if(window.M&&M.Modal){
                    var instance=M.Modal.getInstance(modal)||M.Modal.init(modal);
                    instance.open();
                }
            });
        }
        var form=modal.querySelector('.wpcf7-form');
        var response=form&&form.querySelector('.wpcf7-response-output');
        var submit=form&&form.querySelector('.wpcf7-submit');
        if(response&&submit&&submit.parentNode){
            submit.parentNode.insertBefore(response, submit);
        }
        function syncModalState(){
            document.documentElement.classList.toggle(
                'nousro-spb-question-open',
                modal.classList.contains('open') ||
                (callbackModal && callbackModal.classList.contains('open'))
            );
        }
        new MutationObserver(syncModalState).observe(modal,{attributes:true,attributeFilter:['class']});
        if(callbackModal){
            new MutationObserver(syncModalState).observe(callbackModal,{attributes:true,attributeFilter:['class']});
        }
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

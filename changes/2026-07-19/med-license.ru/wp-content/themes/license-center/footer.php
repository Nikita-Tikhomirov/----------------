<?php
/**
 * The template for displaying the footer
 *
 * Contains the closing of the #content div and all content after.
 *
 * @link https://developer.wordpress.org/themes/basics/template-files/#template-partials
 *
 * @package License_center
 */

?>

<footer class="footer">
    <div class="container">
        <div class="footer-col">
            <div class="footer-logo">
                <a href="/" class="">
                    <?
                    $logo_img = '';
                    if ($custom_logo_id = get_theme_mod('custom_logo')) {
                        $logo_img = wp_get_attachment_image($custom_logo_id, 'full', false, array(
                            'class' => 'custom-logo',
                            'itemprop' => 'logo',
                        ));
                    }

                    echo $logo_img;
                    ?>

                </a>
            </div>
            <div class="footer-copyright"><?php dynamic_sidebar('copyright'); ?></div>
            <div class="footer-address"><?php dynamic_sidebar('adress'); ?></div>
        </div>
        <div class="footer-menu footer-col">
            <?php dynamic_sidebar('footer_1'); ?>
        </div>
        <div class="footer-menu footer-col">
            <?php dynamic_sidebar('footer_2'); ?>
        </div>
        <div class="footer-menu footer-col">
            <?php dynamic_sidebar('footer_3'); ?>
        </div>
        <div class="footer-col">
            <div class="footer-feedback">
                <span class="btn btn-success open-callback">ЗАКАЗАТЬ ЗВОНОК</span>
            </div>
            <div class="calc-button footer-calc"><span class="open-question" style="text-align:left; color:#fff">Задать
                    вопрос</span></div>
            <div class="footer-phone"><?php dynamic_sidebar('phone'); ?></div>
            <div class="footer-email"><?php dynamic_sidebar('email'); ?></div>

        </div>
    </div>
</footer>
<div id="modals">
    <div id="backform" class="popup">
        <?php echo do_shortcode("[contact-form-7 id='52' title='Форма «Бесплатная консультация»']"); ?>
    </div>
</div>
<div id="popup_bg"></div>

<?php wp_footer(); ?>

<!-- Yandex.Metrika counter -->
<script type="text/javascript">
    (function (m, e, t, r, i, k, a) {
        m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments) };
        m[i].l = 1 * new Date(); k = e.createElement(t), a = e.getElementsByTagName(t)[0], k.async = 1, k.src = r, a.parentNode.insertBefore(k, a)
    })
        (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");

    ym(46940253, "init", {
        clickmap: true,
        trackLinks: true,
        accurateTrackBounce: true,
        webvisor: true
    });
</script>
<noscript>
    <div><img src="https://mc.yandex.ru/watch/46940253" style="position:absolute; left:-9999px;" alt="" /></div>
</noscript>
<!-- /Yandex.Metrika counter -->

<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-5727382-22"></script>
<script>
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    gtag('js', new Date());

    gtag('config', 'UA-5727382-22');
</script>


<!-- Попап фон -->
<div class="unipop-overlay" id="unipop-overlay"></div>

<!-- === Попап 1: ЗАКАЗАТЬ ЗВОНОК === -->
<div class="unipop" id="popup-callback">
    <div class="unipop-inner">
        <button class="unipop-close">&times;</button>
        <h2 class="unipop-title">ЗАКАЗАТЬ ЗВОНОК</h2>

        <form class="unipop-form sendFormCustom" data-form="callback">
            <input type="text" name="phone" required placeholder="+7 (___) ___-__-__">

            <input placeholder="Введите цифру пять:" type="text" name="captcha" required>
            <div class="conf">
                <span class="policity">
                    Нажимая на кнопку "Отправить" я даю согласие на обработку персональных данных на условиях <br> <a
                        href="https://www.apreal.ru/konfedencialnost.html" target="_blank">Политики обработки персональных данных</a><br>
                </span>
            </div>
            <input type="hidden" name="page" class="siteUrl">
            <button type="submit" class="unipop-btn">Отправить</button>
            <div class="ajaxConsent">
                Спасибо за Ваше сообщение. Оно успешно отправлено
            </div>
        </form>
    </div>
</div>

<!-- === Попап 2: ЗАДАТЬ ВОПРОС === -->
<div class="unipop" id="popup-question">
    <div class="unipop-inner">
        <button class="unipop-close">&times;</button>
        <h2 class="unipop-title">ЗАДАТЬ ВОПРОС</h2>

        <form class="unipop-form sendFormCustom" data-form="question">
            <textarea name="coment" placeholder="Вопрос"></textarea>
            <input type="tel" name="phone" required placeholder="+7 (___) ___-__-__">
            <input type="text" name="name" placeholder="Имя">
            <input placeholder="Введите цифру пять:" type="text" name="captcha" required>
            <div class="conf">
                <span class="policity">
                    Нажимая на кнопку "Отправить" я даю согласие на обработку персональных данных на условиях <br> <a
                        href="https://www.apreal.ru/konfedencialnost.html" target="_blank">Политики обработки персональных данных</a><br>
                </span>
            </div>
            <input type="hidden" name="page" class="siteUrl">
            <button type="submit" class="unipop-btn">Отправить</button>
            <div class="ajaxConsent">
                Спасибо за Ваше сообщение. Оно успешно отправлено
            </div>
        </form>
    </div>
</div>



<script>
    document.addEventListener('DOMContentLoaded', () => {

        const overlay = document.getElementById('unipop-overlay');
        const popups = document.querySelectorAll('.unipop');

        // --- Открытие ---
        function openPopup(id) {
            overlay.classList.add('active');
            document.getElementById(id).classList.add('active');
        }

        // --- Закрытие ---
        function closePopup() {
            overlay.classList.remove('active');
            popups.forEach(p => p.classList.remove('active'));
        }

        // Закрытие по крестику
        document.querySelectorAll('.unipop-close').forEach(btn => {
            btn.addEventListener('click', closePopup);
        });

        // Закрытие по фону
        overlay.addEventListener('click', closePopup);


        // --- Открытие попапов по классам ---
        document.querySelectorAll('.open-callback').forEach(btn => {
            btn.addEventListener('click', () => {
                openPopup('popup-callback');
            });
        });

        document.querySelectorAll('.open-question').forEach(btn => {
            btn.addEventListener('click', () => {
                openPopup('popup-question');
            });
        });


        // --- Отправка форм ---
        document.querySelectorAll('.sendFormCustom').forEach(form => {
            form.addEventListener('submit', e => {
                e.preventDefault();

                let hidenInput = form.querySelector('.siteUrl')
                let urlNow = window.location.href
                hidenInput.value = urlNow

                let formData = new FormData(form);
                let formConsent = form.querySelector('.ajaxConsent')

                // у формы есть data-form="callback" или data-form="question"
                formData.append('formid', form.dataset.form);

                fetch('/mail.php', {
                    method: 'POST',
                    body: formData
                })
                    .then(r => r.json())
                    .then(data => {
                        if (!data.success) {
                            throw new Error(data.message || 'Ошибка отправки');
                        }
                        formConsent.classList.add('active')
                        setTimeout(() => {
                            closePopup()
                        }, 3000);
                    })
                    .catch(err => {
                        alert(err.message || 'Ошибка отправки');
                    });
            });
        });

    });
</script>
<style>
    .unipop-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.6);
        display: none;
        z-index: 2147483600;
    }

    .unipop-overlay.active {
        display: block;
    }

    .unipop {
        position: fixed;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%) scale(0.8);
        background: #fff;
        width: 600px;
        padding: 30px;
        /* border-radius: 12px; */
        display: none;
        z-index: 2147483601;
        transition: .25s;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3);
    }

    .unipop.active {
        display: block;
        transform: translate(-50%, -50%) scale(1);
    }

    .unipop-close {
        position: absolute;
        right: 10px;
        top: 10px;
        background: #ffffff;
        /* border: 2px solid #000; */
        width: 28px;
        height: 28px;
        font-size: 24px;
        border: none;
        /* border-radius: 50%; */
        cursor: pointer;
    }

    .unipop-title {
        text-align: center;
        font-size: 24px;
        margin-bottom: 40px;
        text-transform: uppercase;
        color: #5db533;

    }

    .unipop-form input {
        width: 100%;
        padding: 0 10px;
        background: #fff;
        color: #666;
        border: 1px solid #e5e5e5 !important;
        display: block;
        padding-left: 10px !important;
        margin-bottom: 15px !important;
        box-sizing: border-box !important;
        height: 40px;
    }

    .unipop-form input::placeholder {
        /* padding-left: 10px !important; */
    }

    .unipop-btn {
        width: fit-content;
        padding: 12px 20px;
        background: #fff;
        color: #333;
        cursor: pointer;
        font-size: 17px;
        border: 1px solid rgba(0, 0, 0, .1);
        display: block;
        margin: auto;
        font-weight: 300;
        text-transform: uppercase;
        font-size: 14px;
    }

    .conf {
        margin-bottom: 20px;
        text-align: center;
        width: 100%;
        font-size: 16px;
    }

    .conf a {
        color: #5db533;
    }

    .wpcf7-form .conf a {
        color: #fff;
        text-decoration: underline;
    }

    .ajaxConsent {
        display: none;
        margin-top: 20px;
        width: 100%;
        font-size: 16px;
        text-align: center;
    }

    .ajaxConsent.active {
        display: block;

    }

    .unipop-form textarea {
        color: #666;
        border: 1px solid #e5e5e5 !important;
        display: block;
        padding-left: 10px !important;
        padding-top: 10px;
        margin-bottom: 15px !important;
        width: 100%;
        font-size: 16px;
        min-height: 70px;
    }



    @media (max-width: 992px) {
        .unipop {
            max-width: calc(100% - 30px);
        }

        .unipop-title {
            font-size: 24px !important;
            margin-bottom: 25px;
        }
    }
</style>
<!-- <button class="open-callback">Открыть</button>
<button class="open-question">Открыть</button> -->

</body>

</html>

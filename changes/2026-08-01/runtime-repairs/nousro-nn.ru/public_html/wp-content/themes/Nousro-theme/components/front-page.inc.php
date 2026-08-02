<main class="page">
    <div class="carousel carousel-slider center customMainSlider">
        <div class="carousel-fixed-item center middle-indicator">
            <div class="left">
                <a href="#" class="movePrevCarousel middle-indicator-text waves-effect waves-light content-indicator"><i
                        class="material-icons left  middle-indicator-text">chevron_left</i></a>
            </div>

            <div class="right">
                <a href="#" class="moveNextCarousel middle-indicator-text waves-effect waves-light content-indicator"><i
                        class="material-icons right middle-indicator-text">chevron_right</i></a>
            </div>
        </div>

        <?php if (have_rows('cat-banner')): ?>
            <?php
            while (have_rows('cat-banner')):
                the_row();
                ?>
                <div class="carousel-item red white-text" href="#one!">

                    <?php
                    $image = get_sub_field('image');

                    if (!empty($image)): ?>

                        <img src="<?php echo $image['url']; ?>" alt="<?php echo $image['alt']; ?>" />

                    <?php endif; ?>
                </div>
            <?php endwhile; ?>
        <?php else: ?>
            <?php if (have_rows('slider', 'option')): ?>

                <?php while (have_rows('slider', 'option')):
                    the_row(); 
                    $link = get_sub_field('link');
                    ?>
                    <a class="carousel-item red white-text" href="<?php echo $link?>">
                        <?php
                        $image = get_sub_field('slide');
                        $imageMob = get_sub_field('banner_mobile');

                        $s_title = get_sub_field('sld_title');
                        $s_text = get_sub_field('sld_text');
                        $s_pos = get_sub_field('sld_pos');
                

                        
                        if (!empty($image)):
                            ?>
                            <picture>
                                <source media="(max-width: 768px)" srcset="<?php echo $imageMob['url']; ?>">
                                <source media="(min-width: 769px)" srcset="<?php echo $image['url']; ?>">
                                <img src="<?php echo $image['url']; ?>" alt="<?php echo $s_title; ?>" />
                            </picture>

                            <div class="qqqs <?php echo $s_pos; ?>">
                                <div class="qqqs__item">
                                    <p class="heading"
                                        style="font-size: 38px;font-weight: bold;text-shadow: -1px 1px 0 #000, 1px 1px 0 #000, 1px -1px 0 #000, -1px -1px 0 #000;">
                                        <?php echo $s_title; ?>
                                    </p>
                                    <p class="subText"
                                        style="font-size: 22px;text-shadow: -1px 1px 0 #000, 1px 1px 0 #000, 1px -1px 0 #000, -1px -1px 0 #000;">
                                        <?php echo $s_text; ?>
                                    </p>
                                </div>
                            </div>

                        <?php endif; ?>
                    </a>
                <?php endwhile; ?>

            <?php endif; ?>

        <?php endif; ?>

    </div>
    <section class="section about-us content" style="background: white;">
        <div class="about-us__text" data-aos="fade-up-right" data-aos-delay="300">
            <!-- <span class="about-us__upTitle">О нашем учебном центре</span> -->
            <h1 class="section__title">Межрегиональный Учебный Центр</h1>

            <div class="about-us__desc">
                <p>Поможем получить необходимое профильное образование или повысить квалификацию. Что же нас отличает от
                    остальных?</p>
                <ul>
                    <li>С 2011 года мы разработали сотни программ по всем актуальным направлениям. Более того, мы готовы
                        написать и согласовать программу обучения для вас;</li>
                    <li>Обучающиеся самостоятельно выбирают удобный формат: очный и дистанционный формат, выездные
                        занятия;</li>
                    <li>Мы всегда готовы сделать скидку для постоянных клиентов или при обучении группы сотрудников</li>
                    <li>Уникальные разработки в онлайн обучении, современное техническое оснащение, а также опытные
                        практики-преподаватели</li>
                </ul>
                <a href="/otkrytaya-informatsiya/" target="_blank">СВЕДЕНИЯ ОБ ОБРАЗОВАТЕЛЬНОЙ ОРГАНИЗАЦИИ</a>
            </div>
        </div>
        <div class="about-us__photo" style="display: flex;align-items: center;justify-content: center;">
            <img src="/wp-content/themes/Nousro-theme/images/nochu-dpo-muc.webp" alt="Сведения об образовательной организации">
        </div>

    </section>

    <style>
        .about-us__text .section__title {
            margin-top: 0;
        }

        .distanceLearning__wrap {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-gap: 80px;
            align-items: center;
        }

        @media screen and (max-width:1024px) {
            .distanceLearning__wrap {
                display: flex;
                flex-direction: column-reverse;
                align-items: center;
                justify-content: center;

            }
        }
    </style>

    <section class="distanceLearning">
        <div class="content">
            <div class="distanceLearning__wrap">
                <div class="distanceLearning__imgWrap">
                    <img src="/wp-content/themes/Nousro-theme/assets/images/distancionnoe-obuchenie.webp"
                        alt="Дистанционное образование" id="remote-img">
                </div>
                <div class="distanceLearning__textWrap">
                    <p class="remote__heading">Дистанционное обучение</p>
                    <p>Дистанционное образование – удобная форма обучения для людей, привыкших рационально использовать
                        свое время. Качество и результат обучения ничем не отличаются от очного обучения. Мы оказываем
                        услуги не только физическим лицам, но и юридическим субъектам для профессиональной подготовки и
                        повышения квалификации их сотрудников.</p>
                    <p>Дистанционное обучение в Межрегиональном Учебном Центре – это прекрасная возможность получить
                        дополнительное профессиональное образование или специальность. Вам предоставляется персональный
                        доступ в личный кабинет, где хранится вся информация о необходимом курсе. Проходить обучение вы
                        можете в удобное для Вас время. Даже после обучения доступ в личный кабинет остается открытым, и
                        вы всегда можете зайти на сайт и освежить свои знания.</p>
                </div>
            </div>
        </div>
    </section>


    <section class="section documents customDocs">
        <div class="documents__wrapper content" style="white-space: nowrap;">
            <h3 class="section__title aos-init aos-animate" data-aos="fade-up-right" data-aos-delay="400"
                data-aos-offset="200">У нас есть все законные основания</h3>

            <!-- Slider main container -->
            <div class="swiper docsCustom">
                <!-- Additional required wrapper -->
                <div class="swiper-wrapper">
                    <!-- Slides -->
                    <div class="swiper-slide col s12 m6">
                        <div class="card horizontal">
                            <div class="card-image">
                                <div class="material-placeholder">

                                    <div class="material-placeholder">
                                        <div class="material-placeholder">
                                            <a data-fslightbox="docs"
                                                href="/wp-content/themes/Nousro-theme/images/licenziya-na-obrazovatelnuyu-deyatelnost.webp"
                                                class="material-placeholder"><img alt="Лицензия на образовательную деятельсность" class=""
                                                    src="/wp-content/themes/Nousro-theme/images/licenziya-na-obrazovatelnuyu-deyatelnost-small.webp"></a>
                                        </div>
                                    </div>
                                    </a>
                                </div>
                            </div>
                            <div class="card-stacked" style="flex: 1;">
                                <div class="card-content">
                                    <p>Лицензия на <br>профессиональное<br> обучение от <br>Департамента<br> образования
                                        Москвы</p>
                                </div>
                                <div class="card-action">
                                    <a href="/dokumenty/">Все документы</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="swiper-slide col s12 m6 ">
                        <div class="card horizontal">
                            <div class="card-image">
                                <div class="material-placeholder">

                                    <div class="material-placeholder">
                                        <div class="material-placeholder">
                                            <a href="/wp-content/themes/Nousro-theme/images/akkreditaciya-ohrana-truda.webp"
                                                data-fslightbox="docs" class="material-placeholder"><img alt="Аккредитация по охране труда" class=""
                                                    src="/wp-content/themes/Nousro-theme/images/akkreditaciya-ohrana-truda-small.webp">
                                            </a>
                                        </div>
                                    </div>

                                </div>
                            </div>
                            <div class="card-stacked" style="flex: 1;">
                                <div class="card-content">
                                    <p>Аккредитация от<br> Министерства труда и<br> социальной защиты<br> Российской
                                        Федерации</p>
                                </div>
                                <div class="card-action">
                                    <a href="/dokumenty/">Все документы</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="swiper-slide col s12 m6 ">
                        <div class="card horizontal">
                            <div class="card-image">
                                <div class="material-placeholder">

                                    <div class="material-placeholder">
                                        <div class="material-placeholder">
                                            <a data-fslightbox="docs"
                                                href="/wp-content/themes/Nousro-theme/images/soglasovanie-program-mchs.webp"
                                                class="material-placeholder"><img alt="Согласования программ" class=""
                                                    src="/wp-content/themes/Nousro-theme/images/soglasovanie-program-mchs-small.webp"></a>
                                        </div>
                                    </div>

                                </div>
                            </div>
                            <div class="card-stacked" style="flex: 1;">
                                <div class="card-content" style="font-size: 13px">
                                    <p>Разработанные<br> программы обучения<br> согласованы<br> Управлением<br> ГПН ГУ
                                        МЧС
                                        РФ,<br> департаментом<br> образования<br> города Москвы и др.</p>
                                </div>
                                <div class="card-action">
                                    <a href="/dokumenty/">Все документы</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="swiper-slide col s12 m6 ">
                        <div class="card horizontal">
                            <div class="card-image">
                                <div class="material-placeholder">

                                    <div class="material-placeholder">
                                        <div class="material-placeholder">
                                            <a data-fslightbox="docs"
                                                href="/wp-content/themes/Nousro-theme/images/sanitarnoe-zakluchenie.webp"
                                                class="material-placeholder"><img alt="Санитарное заключение" class=""
                                                    src="/wp-content/themes/Nousro-theme/images/sanitarnoe-zakluchenie-small.webp"></a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="card-stacked" style="flex: 1;">
                                <div class="card-content" style="font-size: 14px">
                                    <p>Наши<br> учебные помещения<br> имеют<br> положительные<br> заключения<br> ГПН
                                        и<br>
                                        СЭС Роспотребнадзора</p>
                                </div>
                                <div class="card-action">
                                    <a href="/dokumenty/">Все документы</a>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>


                <!-- If we need navigation buttons -->
                <!-- <div class="swiper-button-prev"></div>
                <div class="swiper-button-next"></div> -->
                <div style="display:flex; gap:25px; justify-content:center">
                    <div class="next-arrow" style="
                                           background-image:url('https://static.tildacdn.com/tild3232-6361-4565-b366-373464613938/Group_2.svg');
                                           background-size:cover;
                                           background-repeat:no-repeat;
                                           width:25px;
                                           height:38px;
                                           cursor:pointer;
                                           user-select: none;
                                           "></div>
                    <div class="prev-arrow" style="
                                           background-image:url('https://static.tildacdn.com/tild3232-6361-4565-b366-373464613938/Group_2.svg');
                                           background-size:cover;
                                           background-repeat:no-repeat;
                                           width:25px;
                                           height:38px;
                                           transform:rotate(180deg);
                                           cursor:pointer;
                                           user-select: none;
                                           "></div>
                </div>

            </div>

        </div>
    </section>



    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css" />

    <script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>


    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const swiper = new Swiper('.docsCustom', {
                // Optional parameters

                // Default parameters
                slidesPerView: 1,
                spaceBetween: 20,
                // Responsive breakpoints
                breakpoints: {
                    // when window width is >= 320px

                    // when window width is >= 480px
                    768: {
                        slidesPerView: 2,
                        spaceBetween: 30
                    },
                    // when window width is >= 640px
                    1024: {
                        slidesPerView: 3,
                        spaceBetween: 40
                    }
                },

                // Navigation arrows
                navigation: {
                    nextEl: '.docsCustom .prev-arrow',
                    prevEl: '.docsCustom .next-arrow',
                },

            });

        })


    </script>






    <?php get_template_part('custom/s-request'); ?>

    <section class="section documents" style="background: white;">
        <div class="documents__wrapper content">
            <h3 class="section__title" data-aos="fade-up-right" data-aos-delay="400" data-aos-offset="200">Вы ничем не
                рискуете</h3>
            <div class="customAdvantages"
                style="width:750px; margin:0 auto;display:flex;justify-content:space-between;">
                <div class="sh-card z-depth-3">
                    <img src="/wp-content/themes/Nousro-theme/images/dogovor.webp" alt="Мы вернем деньги,
                        если вас не устроил учебный процесс" style="margin-top: 10px;"
                        align="center">
                    <img src="number.png" alt="Мы вернем деньги,
                        если вас не устроил учебный процесс" width="180px" align="center">
                    <p>НАДЕЖНО</p>
                    <p style="padding-left:8px;padding-right:8px;font-size:10pt;text-align:center;">Мы вернем деньги,
                        если вас не устроил учебный процесс</p>
                </div>
                <div class="sh-card z-depth-3">
                    <img src="/wp-content/themes/Nousro-theme/images/postopata.webp"  alt="Мы являемся
                        участником государственных тендеров" style="margin-top: 10px;"
                        align="center">
                    <img src="number2.png" width="180px" align="center" alt="участники тендеров">
                    <p>УДОБНО</p>
                    <p style="padding-left:8px;padding-right:8px;font-size:10pt;text-align:center;">Мы являемся
                        участником государственных тендеров, поэтому все условия подписанного договора соблюдаются
                        беспрекословно</p>
                </div>
                <div class="sh-card z-depth-3">
                    <img src="/wp-content/themes/Nousro-theme/images/vozvrat.webp" alt="Есть возможность
                        пройти обучение по 100% постоплате" style="margin-top: 10px;"
                        align="center">
                    <img src="number3.png" width="180px" align="center" alt="Есть возможность
                        пройти обучение по 100% постоплате">
                    <p>БЕЗОПАСНО</p>
                    <p style="padding-left:8px;padding-right:8px;font-size:10pt;text-align:center;">Есть возможность
                        пройти обучение по 100% постоплате</p>
                </div>
            </div>
        </div>
    </section>
    <!--  -->



    <section class="section documents sertsCustom" style="background: white;">
        <div class="content">
            <h3 class="section__title" data-aos="fade-up">В результате обучения вы получаете</h3>
            <div class="documents__stall stall" data-aos="fade-up">
                <a href="/kursy/" class="stall__item">
                    <div class="stall-image">
                        <img src="/wp-content/themes/Nousro-theme/images/udostoverenie-povishenie-kvalifikacii.webp"
                            alt="Удостоверение о повышении квалификации">
                    </div>
                    <div class="stall__heading">
                        Удостоверение о повышении квалификации
                    </div>
                    <div class="stall__button">
                        <span class="stall__more">+</span>Подробнее
                    </div>
                </a>
                <a href="/kursy/" class="stall__item">
                    <div class="stall-image">
                        <img src="/wp-content/themes/Nousro-theme/images/sertificat.webp" alt=" Сертификат о прохождении курсов ">
                    </div>
                    <div class="stall__heading">
                        Сертификат о прохождении курсов &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
                    </div>
                    <div class="stall__button">
                        <span class="stall__more">+</span>Подробнее
                    </div>
                </a>

                <a href="/rabochie/" class="stall__item">
                    <div class="stall-image">
                        <img src="/wp-content/themes/Nousro-theme/images/svidetelstvo.webp" alt="Свидетельство о присвоении профессии">
                    </div>
                    <div class="stall__heading">
                        Свидетельство о присвоении профессии
                    </div>
                    <div class="stall__button">
                        <span class="stall__more">+</span>Подробнее
                    </div>
                </a>

                <a href="/profperepodgotovka/" class="stall__item">
                    <div class="stall-image">
                        <img src="/wp-content/themes/Nousro-theme/images/diplom.webp" alt="Диплом о профессиональной переподготовке">
                    </div>
                    <div class="stall__heading">
                        Диплом о профессиональной переподготовке
                    </div>
                    <div class="stall__button">
                        <span class="stall__more">+</span>Подробнее
                    </div>
                </a>

            </div>
        </div>
    </section>
    <!--  -->
    <section>

    </section>
    <!--  -->
<style>
	.clients{
		padding-bottom: 25px;
	}
	.clients .carousel{
		height:80px !important;
	}
</style>
    <section class="section" style="background: white;">
        <div class="clients content">
            <h3 class="section__title">Благодарные клиенты</h3>
            <div class="carousel">

                <a class="carousel-item" href="#one!"><img
                        src="/wp-content/themes/Nousro-theme/images/1client.webp" alt="OOO Дайхманн"
                        title="OOO Дайхманн"></a>

                <a class="carousel-item" href="#two!"><img
                        src="/wp-content/themes/Nousro-theme/images/2client.webp"
                        alt="ООО АйДи-Технологии управления" title="ООО АйДи-Технологии управления"
                        style="height: 60px;"></a>

                <a class="carousel-item" href="#three!"><img
                        src="/wp-content/themes/Nousro-theme/images/3client.webp"
                        alt="Акционерное общество Нокиа Солюшнз энд Нетворкс"
                        title="Акционерное общество Нокиа Солюшнз энд Нетворкс"></a>

                <a class="carousel-item" href="#four!"><img
                        src="/wp-content/themes/Nousro-theme/images/4client.webp"
                        alt="ООО БАЗИС ДЕВЕЛОПМЕНТ" title="ООО БАЗИС ДЕВЕЛОПМЕНТ"></a>

                <a class="carousel-item" href="#five!"><img
                        src="/wp-content/themes/Nousro-theme/images/5client.webp"
                        alt="ФГУП РФЯЦ-ВНИИЭФ" title="ФГУП РФЯЦ-ВНИИЭФ"></a>

                <a class="carousel-item" href="#five!"><img
                        src="/wp-content/themes/Nousro-theme/images/6client.webp"
                        alt="ООО Банк БЦК-Москва" title="ООО Банк БЦК-Москва"></a>

                <a class="carousel-item" href="#five!"><img
                        src="/wp-content/themes/Nousro-theme/images/7client.webp"
                        alt="ООО БЕБЕЛЬ" title="ООО БЕБЕЛЬ"></a>

                <a class="carousel-item" href="#five!"><img
                        src="/wp-content/themes/Nousro-theme/images/8client.webp"
                        alt="ООО Аякс" title="ООО Аякс"></a>

                <a class="carousel-item" href="#five!"><img
                        src="/wp-content/themes/Nousro-theme/images/9client.webp" alt="АО НИКИЭТ"
                        title="АО НИКИЭТ"></a>

                <a class="carousel-item" href="#five!"><img
                        src="/wp-content/themes/Nousro-theme/images/10client.webp"
                        alt="СтомАтриум" title="СтомАтриум"></a>

                <a class="carousel-item" href="#five!"><img
                        src="/wp-content/themes/Nousro-theme/images/11client.webp"
                        alt="ООО Медстрой" title="ООО Медстрой"></a>

                <a class="carousel-item" href="#five!"><img
                        src="/wp-content/themes/Nousro-theme/images/12client.webp"
                        alt="ООО ЭРА" style="height: 40px;"></a>

                <a class="carousel-item" href="#five!"><img
                        src="/wp-content/themes/Nousro-theme/images/13client.webp"
                        alt="Эко-Город" title="Эко-Город"></a>

                <a class="carousel-item" href="#five!"><img
                        src="/wp-content/themes/Nousro-theme/images/14client.webp"
                        alt="АО Металлургический завод ЭЛЕКТРОСТАЛЬ" title="АО Металлургический завод ЭЛЕКТРОСТАЛЬ"></a>

                <a class="carousel-item" href="#five!"><img
                        src="/wp-content/themes/Nousro-theme/images/15client.webp"
                        alt="ООО АЭГ" title="ООО АЭГ"></a>
            </div>
        </div>
    </section>
    <section class="section questions">
        <div class="content" style="height: 540px">
            <section class="section first-screen" style="padding-bottom: 0px;padding-top:25px;">
                <div class="content">
                    <div class="row" style="margin-bottom: 0px;">
                        <div class="col s12 m12">
                            <div class="card horizontal"
                                style="background: transparent;margin-top: 0px;margin-bottom: 0px;box-shadow:none;">
                                <div class="card-image hide-on-med-and-down aos-init aos-animate"
                                    data-aos="fade-up-right" data-aos-delay="300"
                                    style="position: relative;background: white;">
                                    <!-- <img src="/wp-content/themes/Nousro-theme/assets//images/edu.jpg"> -->
                                    <!-- <img src="/wp-content/themes/Nousro-theme/assets/images/slide_3_img.png" alt=""> -->
                                    <img src="/wp-content/themes/Nousro-theme/assets/images/monitor.png" alt="Онлайн запись">
                                    <iframe class="iv-i" style="display:block;margin:0;padding:0;border:0;"
                                        src="//open.ivideon.com/embed/v2/?server=100-df51ed894c1e20f0d1ccd6e9d091a676&amp;camera=0&amp;width=&amp;height=&amp;lang=ru&amp;ap"
                                        allowfullscreen="" width="100%" height="150" frameborder="0"></iframe>
                                </div>
                                <div class="questions__advatages advatages">
                                    <h3 class="questions__title">Наши преимущества</h3>
                                    <div class="advatages__item">
                                        <div class="advatages__image"><img
                                                src="/wp-content/themes/Nousro-theme/assets/images/adv-ico1.png" alt="250 учебных программ">
                                        </div>
                                        <div class="advatages__text"><strong>Более 250 учебных программ,</strong>в том
                                            числе курсы, согласованные в МЧС, Министерстве труда и ФСТЭК.</div>
                                    </div>
                                    <div class="advatages__item">
                                        <div class="advatages__image"><img
                                                src="/wp-content/themes/Nousro-theme/assets/images/adv-ico2.png" alt="Соответствие профстандартам">
                                        </div>
                                        <div class="advatages__text"><strong>Соответствие образовательных программ
                                                профстандартам, </strong>федеральным государственным требованиям и
                                            требованиям национальных объединений.</div>
                                    </div>
                                    <div class="advatages__item">
                                        <div class="advatages__image"><img
                                                src="/wp-content/themes/Nousro-theme/assets/images/adv-ico3.png" alt="Опытные профессоры преподователи">
                                        </div>
                                        <div class="advatages__text"><strong>Опытный профессорско-преподавательский
                                                состав, </strong>состоящий из экспертов и ведущих специалистов в своей
                                            области.</div>
                                    </div>
                                    <div class="advatages__item">
                                        <div class="advatages__image"><img
                                                src="/wp-content/themes/Nousro-theme/assets/images/adv-ico4.png" alt="Дистанционное обучение">
                                        </div>
                                        <div class="advatages__text"><strong>Использование современных дистанционных
                                                образовательных технологий,</strong>позволяющих слушателям проходить
                                            обучение в индивидуальном темпе, находясь в любой точке России.</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- <img class="section-bg" src="/wp-content/themes/Nousro-theme/assets/letter.png" alt=""> -->
            </section>
        </div>
    </section>




<?php get_template_part('custom/s-blog'); ?>
    <section class="pre-footer"></section>

</main>


<script>

    // 
    // Main Page Form
    // 
    document.addEventListener('DOMContentLoaded', function () {
    if (!window.Vue || !document.getElementById('formApp')) return;
    var froma = new Vue({
        el: '#formApp',
        data: {
            message: 'Hello Vue!',
            toggleOption: '',
            name: '',
            nameError: {
                text: ''
            },
            active_index: 0,
            active_q: {},
            questions: [
                {
                    qu: 'Цель',
                    variqtions: [
                        {
                            val: '1',
                            id: '1',
                            message: 'Обучение'
                        },
                        {
                            val: '2',
                            id: '2',
                            message: 'Повышение квалификации'
                        },

                        {
                            val: '3',
                            id: '3',
                            message: 'Профессиональная переподготовка'
                        }
                    ]
                },
                {
                    qu: 'Количество обучающихся?',
                    variqtions: [
                        {
                            val: '1',
                            id: '1',
                            message: 'Один человек'
                        },
                        {
                            val: '2',
                            id: '2',
                            message: 'От 2 до 5 человек'
                        },

                        {
                            val: '3',
                            id: '3',
                            message: 'Более пяти человек'
                        }
                    ]
                },
                {
                    qu: 'Договор',
                    variqtions: [
                        {
                            val: '1',
                            id: '1',
                            message: 'От юр. лица'
                        },
                        {
                            val: '2',
                            id: '2',
                            message: 'От физ. лица'
                        },
                    ]
                }
            ],
            showForm: false,
            checkedNames: [],
            chekedItems: [],
            errors: []
        },
        methods: {
            nameValidate() {
            },
            checkForm: function (e) {
            },
            append(e) {
                e.preventDefault();
                if (this.active_index >= 3) {
                    this.showForm = true;
                } else {
                    this.active_q = null,

                        this.active_q = this.questions[this.active_index];
                    this.checkedNames.push(
                        {
                            'name': this.active_q.qu,
                            'val': ''
                        });
                    this.active_index++;
                }
            },
            send() {
                console.log('Otpravim');
            }
        },
        mounted() {
            this.active_q = this.questions[0];
        }
    });
    });
    // 
    // ./Main Page Form
    // 



</script>
<script>
    document.addEventListener('DOMContentLoaded', function () {
    const dermo = document.querySelectorAll('.docsCustom .col.s12.m6');
    const next = document.querySelector('.next-arrow');
    const prevA = document.querySelector('.prev-arrow');
    const sliderCont = document.querySelector('.sliderCont');
    if (!dermo.length || !next || !prevA || !sliderCont) return;
    const widthEl = dermo[0].offsetWidth + 20;
    let currentEl = 0;

    prevA.addEventListener('click', function () {
        if (currentEl >= dermo.length - 1) return; // Исправлено условие

        sliderCont.scrollTo({
            left: sliderCont.scrollLeft + widthEl,
            behavior: 'smooth'
        });
        currentEl++;
    });

    next.addEventListener('click', function () {
        console.log(1234);
        if (currentEl <= 0) return;

        sliderCont.scrollTo({
            left: sliderCont.scrollLeft - widthEl,
            behavior: 'smooth'
        });
        currentEl--;
    });
    });
</script>
<script>
    setTimeout(() => {
        // move next carousel
        jQuery('.moveNextCarousel').click(function (e) {
            e.preventDefault();
            e.stopPropagation();
            jQuery('.carousel').carousel('next');
        });

        // move prev carousel
        jQuery('.movePrevCarousel').click(function (e) {
            e.preventDefault();
            e.stopPropagation();
            jQuery('.carousel').carousel('prev');
        });
    }, 1000);
</script>

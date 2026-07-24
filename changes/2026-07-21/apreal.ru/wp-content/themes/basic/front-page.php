<?php  get_header();
require_once('components/navbar.inc.php');
?>
<!--Main Navigation-->
<!--Slider-->
<div class="uk-position-relative uk-visible-toggle uk-light main-slider" tabindex="-1" uk-slideshow="min-height: 300; max-height: 350;autoplay: true;">

<ul class="uk-slideshow-items">
	<?php $isSliderExist = false; ?>
	<?php if( have_rows('slider') ): ?>
		<?php
		while( have_rows('slider') ): the_row();

			// vars
			$slide1 = get_sub_field('slide-1');
			$slide2 = get_sub_field('slide-2');
			$slide3 = get_sub_field('slide-3');
			// print_r($text);
			// print_r($link);
			?>
				<?php if($slide1 && $slide1 != null): ?>
				<li class="custom-slider">
					<?php echo $slide1; $isSliderExist = true; ?>
				</li>
				<?php endif; ?>
				<?php if($slide2 && $slide2 != null): ?>
				<li class="custom-slider">
					<?php echo $slide2; $isSliderExist = true; ?>
				</li>
				<?php endif; ?>
				<?php if($slide3 && $slide3 != null): ?>
				<li class="custom-slider">
					<?php echo $slide3; $isSliderExist = true; ?>
				</li>
				<?php endif; ?>

		<?php endwhile; ?>
	<?php else:?>
		<?php if( have_rows('slider', 'option') ): ?>

			<?php while( have_rows('slider', 'option') ): the_row(); ?>
				<li class="custom-slider">
					<?php the_sub_field('slide'); ?>
				</li>
			<?php endwhile; ?>

		<?php endif; ?>

	<?php endif; ?>

	<?php if(!$isSliderExist): ?>

	<?php endif; ?>
</ul>

	<a class="uk-position-center-left-out" href="#" uk-slider-item="previous">...</a>
        <a class="uk-position-center-right-out" href="#" uk-slider-item="next">...</a>


</div>
<!--Slider-->
<div class="uk-container content-area">
    <!--Grid column-->
    <article class="uk-article">



        <div uk-grid>
            <div class="uk-width-1-4@m">
                <?php get_sidebar('main'); ?>
            </div>
            <div class="uk-width-expand@m notForCopy">

                <p class="uk-article-meta">
                    <!--  -->
                    <!--  -->
                    <!--  -->
                    <!--  -->
                    <!--  -->
                    <main id="main" class="site-main" role="main">

                        <!-- /шапка -->
                        <!-- шапка -->
<!-- 						<noindex>
						<nofollow>


						<div class="" style="opacity: 1; padding:20px;background-color: #a4d4eb;margin-bottom: 35px;">
                            <table style="margin-bottom: 0px;">
<tbody>
<tr>
<td>
<p style="text-align: center;">Уважаемые коллеги!</p>
	<a style="margin-top: 5px;display:inline-block;float:none;margin-right:10px;width:100%;"><img src="https://nousro.ru/masks.jpg"></a>
<p>В период с 30 марта по 31 мая включительно мы работаем в усиленном режиме в связи с увеличением обращений по медицинским направлениям услуг, а также дистанционным обучением.</p>
<p>Наши менеджеры, юристы, преподаватели остаются на связи, отгрузка оборудования будет производиться по предварительной договоренности.
По лицензированию в рабочем порядке собираем документы, которые будут поданы в соответствии с графиком работы государственных органов. Обмен оригиналами по возможности откладываем до конца недели.</p>
<p>Обучение проводится только дистанционно.
Одновременно сообщаем, что вся деятельность проводится максимально дистанционно, электронно, для того, чтобы не стать участниками распространения инфекции и сохранить здоровье окружающих людей.</p>
<p>Законы не отменены, торги не отменены, банки работают, счета приходят, мир живет. Сейчас самое время руководителям компаний подготовиться к реализации новых проектов и направлений, на которые в обычное время не хватает времени.</p>
<p>САМОИЗОЛЯЦИЯ не значит БЕЗДЕЙСТВИЕ.</p>
</td>
</tr>
</tbody>
</table>

							</div>
							</nofollow></noindex> -->
                        <!-- инфографика -->
                        <div class="infographic">
                            <div class="info1 info-element" style=""></div><div class="info-description desc1" style="color: rgb(46, 46, 46);">Выберите раздел</div>
                            <div class="info2 info-element act" style=""></div><div class="info-description desc2" style="color: rgb(46, 46, 46);">Ознакомьтесь с информацией</div>
                            <div class="info3 info-element" style=""></div><div class="info-description desc3" style="color: rgb(46, 46, 46);">Закажите обратный звонок</div>
                            <div class="info4 info-element" style=""></div><div class="info-description desc4" style="color: rgb(46, 46, 46);">Свяжитесь с нами</div>
                            <div class="info5 info-element"></div><div class="desc5 info-description" style="color: rgb(46, 46, 46);">Получите интересующий Вас комплекс услуг!</div>
                            <div class="detail"></div>
                            <div class="arrow" style="left: 206px;"></div>

                            <div class="text1 info-texts" style="display: none; opacity: 1;">
                                <ul>
                                    <li><a href="/info.html" rel="nofollow">Лицензирование</a></li>
                                    <li><a href="/obuchenie.html" rel="nofollow">Обучение</a></li>
                                    <li><a href="/oborydovanie.html" rel="nofollow">Оборудование</a></li>
                                    <li><a href="/pages_2/gotovie_1.htm" rel="nofollow">Вступление в СРО</a></li>
                                </ul>
                            </div>

								<div class="text2 info-texts" style="opacity: 1; display: block;"><a href="/info.html" rel="nofollow">На нашем сайте вы можете ознакомиться со всей информацией, касающейся нашей деятельности.</a></div>

                            <div class="text3 info-texts" style="opacity: 1; display: none;">
                                <form id="apreal-inline-callback" action="<?php echo esc_url(home_url('/saver2.php')); ?>" method="post">
                                    <div class="inp1">
                                        <label for="inline-phone-name">Ваше имя</label>
                                        <input type="text" name="phone-name" id="inline-phone-name" autocomplete="name">
                                    </div>
                                    <div class="inp2">
                                        <label for="inline-phone-phone">Телефон</label>
                                        <input type="tel" name="phone-phone" id="inline-phone-phone" autocomplete="tel" required>
                                    </div>
                                    <input type="text" name="company" value="" tabindex="-1" autocomplete="off" style="position:absolute;left:-10000px" aria-hidden="true">
                                    <div class="inp3">
                                        <input type="submit" value="Перезвонить" onclick="if (window.yaCounter6385843) { yaCounter6385843.reachGoal('btn-infograf'); }">
                                    </div>
                                </form>
                                <div class="apreal-inline-callback-result" hidden>
                                    <button type="button" class="apreal-inline-callback-close" aria-label="Закрыть">&times;</button>
                                    <p></p>
                                </div>
                            </div>

                            <style>
                            .text3.info-texts {
                                position: absolute;
                                top: 0;
                                left: 0;
                                box-sizing: border-box;
                                width: 736px;
                                height: 108px;
                                padding: 0;
                                text-align: left;
                            }
                            #apreal-inline-callback {
                                display: grid;
                                grid-template-columns: 240px 240px max-content;
                                gap: 22px;
                                align-items: end;
                                position: relative;
                                width: 100%;
                                padding: 10px 0 0;
                                box-sizing: border-box;
                            }
                            #apreal-inline-callback label {
                                display: block;
                                margin: 0 0 4px;
                                color: #a1a1a1;
                                font-size: 12px;
                                line-height: 16px;
                            }
                            #apreal-inline-callback input[type="text"],
                            #apreal-inline-callback input[type="tel"] {
                                box-sizing: border-box;
                                width: 240px;
                                height: 42px;
                                padding: 8px 10px;
                                border: 1px solid #036fc6;
                                border-radius: 3px;
                                background: #fff;
                                font-size: 16px;
                                line-height: 24px;
                            }
                            #apreal-inline-callback .inp1,
                            #apreal-inline-callback .inp2,
                            #apreal-inline-callback .inp3 {
                                position: static !important;
                                top: auto !important;
                                left: auto !important;
                                right: auto !important;
                                bottom: auto !important;
                                width: auto !important;
                                height: auto !important;
                                margin: 0 !important;
                                transform: none !important;
                                float: none !important;
                            }
                            #apreal-inline-callback .inp3 input[type="submit"] {
                                position: static !important;
                                top: auto;
                                left: auto;
                                right: auto;
                                bottom: auto;
                                transform: none;
                                box-sizing: border-box;
                                min-width: 122px;
                                height: 42px;
                                padding: 0 14px;
                            }
                            #apreal-inline-callback[hidden],
                            .apreal-inline-callback-result[hidden] {
                                display: none !important;
                            }
                            .apreal-inline-callback-result {
                                box-sizing: border-box;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                width: 100%;
                                height: 100%;
                                padding: 30px 36px 20px 12px;
                                text-align: center;
                            }
                            .apreal-inline-callback-result p {
                                margin: 0;
                                font-size: 18px;
                                line-height: 1.4;
                            }
                            .apreal-inline-callback-close {
                                position: absolute;
                                top: 6px;
                                right: 8px;
                                padding: 0;
                                border: 0;
                                background: transparent;
                                color: #333;
                                font-size: 28px;
                                line-height: 1;
                                cursor: pointer;
                            }
                            </style>

                            <script>
                            document.addEventListener('DOMContentLoaded', function () {
                                var form = document.getElementById('apreal-inline-callback');
                                if (!form) {
                                    return;
                                }

                                var result = form.parentNode.querySelector('.apreal-inline-callback-result');
                                var message = result.querySelector('p');
                                var close = result.querySelector('.apreal-inline-callback-close');
                                var submit = form.querySelector('[type="submit"]');

                                form.addEventListener('submit', function (event) {
                                    event.preventDefault();
                                    submit.disabled = true;

                                    fetch(form.action, {
                                        method: 'POST',
                                        body: new FormData(form),
                                        credentials: 'same-origin'
                                    })
                                        .then(function (response) { return response.json(); })
                                        .then(function (response) {
                                            if (!response.success) {
                                                throw new Error(response.data && response.data.message ? response.data.message : 'Не удалось отправить сообщение.');
                                            }
                                            form.hidden = true;
                                            message.textContent = 'Спасибо за Ваше сообщение. Оно успешно отправлено';
                                            result.hidden = false;
                                            form.reset();
                                        })
                                        .catch(function (error) {
                                            message.textContent = error.message;
                                            result.hidden = false;
                                        })
                                        .then(function () {
                                            submit.disabled = false;
                                        });
                                });

                                close.addEventListener('click', function () {
                                    result.hidden = true;
                                    message.textContent = '';
                                    form.hidden = false;
                                });
                            });
                            </script>

                            <div class="text4 info-texts" style="opacity: 1; display: none;">
                                <span class="town">г.Москва</span><br>Краснобогатырская, дом 19А
                                <div class="inp4">+7 495 137 54 58<br>+7 800 505 76 47</div>
                            </div>
                        </div>
                        <!-- инфографика -->
                        <!-- /шапка -->


                        <article>
                        <header class="entry-header">
                                <h1 class="entry-title">Группа Компаний «АП-Риал»</h1>	</header><!-- .entry-header -->

                            <div class="entry-content">
                                <p style="text-align: left; color: #036fc6;"><strong>Мы оказываем ПРАКТИЧЕСКОЕ содействие при взаимодействии бизнеса с государственными органами с целью лицензирования или получения необходимых Вам разрешающих документов в максимально короткие сроки.</strong></p>
                        <p><strong>На страницах нашего сайта Вы можете ознакомиться с предоставляемыми услугами, среди которых:</strong></p>
                        <ul>
                        <li><a title="Лицензирование ФСТЭК" href="/litsenzii_fstek.htm" target="_blank" alt="Лицензирование ФСТЭК">Лицензирование ФСТЭК</a> по деятельности технической защите конфиденциальной информации;</li>
                        <li>Лицензирование работ по <a title="Лицензия на реставрацию" href="/minkult/restavraciya.html" target="_blank" alt="Лицея на реставрацию">реставрации</a> объектов культурного наследия;</li>
                        <li><a title="Лицензия МЧС" href="/licenzija_mchs.html" target="_blank" alt="Лицензия МЧС">Лицензия МЧС</a> для работ по монтажу, техническому обслуживанию и ремонту средств обеспечения пожарной безопасности зданий и сооружений;</li>
                        <li><a title="Лицензия на отходы" href="/rtnadzor-obra.htm" target="_blank" alt="Лицензия на отходы">Лицензирование обращения с отходами</a>, деятельность по сбору, использованию, обезвреживанию, транспортировке, размещению отходов I-IV класса опасности;</li>
                        <li>Лицензирование работ по эксплуатации взрывопожароопасных производственных объектов;</li>
                        <li>Оформление фармацевтических, медицинских, алкогольных и др. видов лицензий;</li>
                        <li>Получение заключений Роспотребнадзора на различные виды деятельности, аккредитация МЧС на проведение экспертизы и оценки пожарных рисков, регистрация электролабораторий;</li>
                        <li>многое другое.</li>
                        </ul>
                        <div class="infographic2-title">3 главные составляющие нашей работы</div>
                        <div class="infographic2">
                            <div class="infographic-slide" style="top: 121px;"></div>
                            <div id="slide1" class="slide1 infographic-element"><div class="title">Надежность</div>В бизнесе ошибки равны потере денег. И чем серьезнее ошибка, тем большие потери вы несете. А сколько штрафов и дополнительных расходов Вас подстерегает на каждом шагу! Мы избавим Вас от ненужных затрат!</div>
                            <div id="slide2" class="slide2 infographic-element"><div class="title">Профессионализм</div>Наши специалисты 5 лет учатся в ВУЗе, затем получают опыт в государственных органах и других структурах в течение такого же срока как минимум. А это более 10 лет получения знаний и опыта в узкой сфере.</div>
                            <div id="slide3" class="slide3 infographic-element"><div class="title">Скорость</div>Сроки выполнения для каждой услуги разные, но мы гарантируем, что они будут настолько короткими, насколько это вообще возможно.<br>Ваша проблема будет решена! На любом этапе ее возникновения.</div>
                        </div>
                        <h2>В бизнесе ошибки равны потере денег. И чем серьезнее ошибка, тем большие потери вы несете.</h2>
                        <p><img class="alignleft" src="/images/graph.jpg" alt="" align="right">Многие предприниматели думают, что они запросто смогут разобраться во всем самостоятельно. Сравним несколько цифр. Каждый наш специалист 5 лет учился в ВУЗе, затем получал опыт в государственных органах и других структурах в течение такого же срока как минимум. А это более 10 лет получения знаний и опыта в узкой сфере. И теперь те, кто уверен, что сможет обработать такое же количество данных за совсем короткий срок – предположим, два месяца. Кто может проследить постоянно меняющееся законодательство по каждому вопросу.</p>
                        <h2>К любой структуре нужно знать свой подход. А могут его знать только те, кто постоянно с ней работает, то есть мы.</h2>
                        <p>Чувствуете разницу? Как Вы думаете, кто из них успешно завершит все процедуры и получит необходимые документы, а кто будет обивать пороги организаций и разбираться в ворохе законов еще очень долго?</p>
                        <p>А сколько штрафов и дополнительных расходов Вас подстерегает на каждом шагу!</p>
                        <p>Если Вы устали от них, устали от того, что не знаете, как решить очередную проблему, позвоните нам, и мы избавим Вас от ненужных затрат.</p>
                        <p>Сроки выполнения для каждой услуги разные, но мы гарантируем, что они будут настолько короткими, насколько это вообще возможно.</p>
                        <p>Решите проблемы с разрешительными документами раз и навсегда!</p>
                        <p><strong>Если Вы не имеете понятия о том, что от вас хотят гос. органы, какие документы вам нужны, что Вы должны им, то в первую очередь обратитесь к нам!</strong></p>
                                    </div><!-- .entry-content -->

                            <footer class="entry-footer">
                            </footer><!-- .entry-footer -->
                        </article><!-- #post-## -->

                            <!-- футер -->

                        </main>
                    <!--  -->
                    <!--  -->
                    <!--  -->
                    <!--  -->
                    <!--  -->
                </p>

				<?php

					if(get_field('page_footer'))
					{
						echo '<div>' . get_field('page_footer') . '</div>';
					}elseif(get_field('page_footer-g', 'options')){
						echo '<div>' . get_field('page_footer-g', 'options') . '</div>';
					}

				?>

            </div>
            <div class="uk-width-1-6@m">

				<?php get_sidebar('right'); ?>
            </div>
        </div>

    </article>
    <!--Grid column-->

</div>
<script>
document.getElementById('slide1').classList.add('infographic-element-active');
	sld();
	function sld(){
		setTimeout(
			() => {
				document.getElementById('slide1').classList.remove('infographic-element-active');
				document.getElementById('slide2').classList.add('infographic-element-active');
				setTimeout( () => {
					document.getElementById('slide2').classList.remove('infographic-element-active');
					document.getElementById('slide3').classList.add('infographic-element-active');
					setTimeout( () => {
						document.getElementById('slide3').classList.remove('infographic-element-active');
						document.getElementById('slide1').classList.add('infographic-element-active');
						sld();
					}, 5000);
				}, 5000);
			}, 5000
		);
	}
</script>
<?php
get_footer();
?>

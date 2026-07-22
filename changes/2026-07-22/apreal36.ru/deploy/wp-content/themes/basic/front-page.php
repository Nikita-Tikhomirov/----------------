<?php get_header(); ?>

<!--Main Navigation-->
<header>

    <?php require_once('components/navbar.inc.php'); ?>

</header>
<!--Main Navigation-->

<!--Main layout-->
<main>
    <!--Slider-->
    <div class="uk-position-relative uk-visible-toggle uk-light main-slider" tabindex="-1" uk-slideshow="min-height: 300; max-height: 350;autoplay: true;">

        <ul class="uk-slideshow-items" style="margin: 0px auto;">
			<?php if( have_rows('slider', 'option') ): ?>

			<?php while( have_rows('slider', 'option') ): the_row(); ?>
				<li class="custom-slider">
					<?php the_sub_field('slide'); ?>
				</li>
			<?php endwhile; ?>

		<?php endif; ?>
<!--             <li class="custom-slider" style="opacity:0;">
                <p class="custom-slider__title">Повышение квалификации сотрудников в нашем учебном центре:</p>
                <ul style="list-style:none;">
                    <li>- Быстро</li>
                    <li>- Качественно</li>
                    <li>- Эффективно</li>
                </ul>
            </li>
            <li class="custom-slider" style="opacity:0;">
                <p class="custom-slider__title">Необходимое оборудование для лицензии МЧС</p>
                <p class="custom-slider__text">Вы можете получить с помощью нашей услуги - доставки <br>
                    Благодаря нашим лабораториям на колесах все нужное оборудование будет у Вас!</p>
            </li> -->
        </ul>

        <a class="uk-position-center-left uk-position-small uk-hidden-hover" style="opacity:0;" href="#" uk-slidenav-previous uk-slideshow-item="previous"></a>
        <a class="uk-position-center-right uk-position-small uk-hidden-hover" style="opacity:0;" href="#" uk-slidenav-next uk-slideshow-item="next"></a>

    </div>
    <!--Slider-->
    <div class="uk-container content-area">

        <?php
        if (have_posts()) {
            $counter = 1;
            while (have_posts()) {
                the_post();
                ?>

                <!--Grid column-->
                <article class="uk-article">
                    <!-- Featured image
                            <div class="view overlay hm-white-slight rounded z-depth-2 mb-4">
                                <?php the_post_thumbnail('medium-large', array('class' => 'img-fluid')); ?>
                            </div> -->
                    <div uk-grid>
                        <div class="uk-width-1-4@m">
                            <?php get_sidebar('main'); ?>
                        </div>
                        <div class="uk-width-expand@m notForCopy">
<!--                             <noindex>
						<nofollow>
							
							
						<div class="" style="opacity: 1; padding:20px;background-color: #a4d4eb;margin-bottom: 35px;">
                            <table style="margin-bottom: 0px;">
<tbody>
<tr>
<td>
<p style="text-align: center;">Уважаемые клиенты!</p>
	<a href="https://go.mywebinar.com/drcl-skzt-jvzn-msnf" style="margin-top: 5px;display:inline-block;float:none;margin-right:10px;width:100%;"><img src="https://nousro.ru/masks.jpg"></a>
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
                            <h1 class="uk-article-title">
                                <strong><?php the_title(); ?></strong>
                            </h1>
                            <p class="uk-article-meta"><?php the_content(); ?></p>
                        </div>
                        <div class="uk-width-1-6@m">
                            <div class="uk-button uk-button-danger open-question" style="font-size: 14px;padding-left: 0px;padding-right: 0px;width: 100%;"> <span class="uk-button-danger__inner">Задать вопрос</span></div>
                            <?php get_sidebar('right'); ?>
                        </div>
                    </div>

                </article>
                <!--Grid column-->

                <?php
                if ($counter % 3 == 0) {
                    ?>
                </div>
                <!--Grid row-->
                <!--Grid dynamic row-->
                <div class="">
                <?php
            }
            $counter++;
        } // end while
    } // end if
    ?>
    </div>
</main>

<?php get_footer(); ?>

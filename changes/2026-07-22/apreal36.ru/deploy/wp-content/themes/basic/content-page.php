<?php  get_header();
require_once('components/navbar.inc.php');
if ( have_posts() ) {
while ( have_posts() ) {
the_post();
?>
<!--Main Navigation-->
<!--Slider-->
<div class="uk-position-relative uk-visible-toggle uk-light main-slider" tabindex="-1" uk-slideshow="min-height: 300; max-height: 350">

<ul class="uk-slideshow-items">
	<li class="custom-slider">
		<!-- <img src="https://getuikit.com/docs/images/photo.jpg" alt="" uk-cover> -->
		<p class="custom-slider__title">Повышение квалификации сотрудников в нашем учебном центре:</p>
		<ul style="list-style:none;">
			<li>- Быстро</li>
			<li>- Качественно</li>
			<li>- Эффективно</li>
		</ul>
	</li>
	<li class="custom-slider">
		<!-- <img src="https://getuikit.com/docs/images/dark.jpg" alt="" uk-cover> -->
		<p class="custom-slider__title">Необходимое оборудование для лицензии МЧС</p>
			<p class="custom-slider__text">Вы можете получить с помощью нашей услуги - доставки <br>
			Благодаря нашим лабораториям на колесах все нужное оборудование будет у Вас!</p>
	</li>
	<!-- <li>
		<img src="https://getuikit.com/docs/images/light.jpg" alt="" uk-cover> 
	</li> -->
</ul>

<a class="uk-position-center-left uk-position-small uk-hidden-hover" href="#" uk-slidenav-previous uk-slideshow-item="previous"></a>
<a class="uk-position-center-right uk-position-small uk-hidden-hover" href="#" uk-slidenav-next uk-slideshow-item="next"></a>

</div>
<!--Slider-->
<div class="uk-container content-area">
    <!--Grid column-->
    <article class="uk-article">

		
        <!-- Featured image
        <div class="view overlay hm-white-slight rounded z-depth-2 mb-4">
            <?php the_post_thumbnail( 'medium-large', array( 'class'=> 'img-fluid')); ?>
        </div> -->
        <div uk-grid>
            <div class="uk-width-1-4@m">
                <?php get_sidebar('main'); ?>
            </div>
            <div class="uk-width-expand@m notForCopy">
				
				<!-- BreadCrumbs -->
				<?php if( have_rows('field') ): ?>
					<ul class="uk-breadcrumb ap-breadcrumb">
						<li><a href="#" class="breadcrumb-back">Назад</a></li>
						<li class="main-page"><a href="/">Главная</a></li>
					<?php
					while( have_rows('field') ): the_row(); 
						
						// vars
						$text = get_sub_field();
						$link = get_sub_field('link');
						// print_r($text);
						// print_r($link);
						?>

							<li><a href="<?php echo $link['link']; ?>"><?php echo $link['text']; ?></a></li>
						
					<?php endwhile; ?>
						<li><span><?php the_title(); ?></span></li>
					</ul>
				<?php endif; ?>
				<!-- ./Breadcrumbs -->
				<!-- <ul class="uk-breadcrumb ap-breadcrumb">
					<li><a href="#" class="breadcrumb-back">Назад</a></li>
					<li class="main-page"><a href="#">Item</a></li>
					<li><a href="#">Item</a></li>
					<li class="uk-disabled"><a>Disabled</a></li>
					<li><span>Active</span></li>
				</ul> -->
                <h1 class="uk-article-title">
                    <strong><?php the_title(); ?></strong>
                </h1>
                <p class="uk-article-meta"><?php the_content(); ?></p>
            </div>
            <div class="uk-width-1-6@m">
            <div class="uk-button uk-button-danger open-question" style="font-size: 14px;padding-left: 0px;padding-right: 0px;width: 100%;">Задать вопрос</div>
                        <?php get_sidebar('right'); ?>
            </div>
        </div>
        
    </article>
    <!--Grid column-->

    <!-- Recent Posts -->
<?php if ( $_COOKIE['viewedProd'] && is_front_page() == false ){ 
    ?>
	<style>
	.recent__title{

	}
	.recent{
		
	}	
	.recent__item{
		margin-left:5px;
		margin-right:5px;
		display: flex;
		flex-direction: column;
		width: calc(25% - 10px);
	}
	.recent__wrapper{
		display: flex;
		flex-wrap: wrap;
		margin-bottom: 30px;
	}
	.recent__title{
		background:#e2eff8;
		padding-top: 5px;
		padding-left: 10px;
		padding-right: 10px;
	}
	.c{
		transition: all .5s;
	}
	.recent__cont{
		overflow:hidden;
		max-height: 140px;
	}
	.recent__img:hover{
		transform: scale(1.1);
	}
	@media(max-width: 992px){
		.recent__item{
			width: 100%;
			margin-top: 10px;
			margin-bottom: 10px;
		}
		.recent__cont{
			display:none;
		}
		.recent__cont{
			display:none;
		}
	}
	</style>
	<div class="recent">
		<h3>Ранее вы смотрели:</h3>
		<div class="recent__wrapper">
		<?php 
			//get_sidebar();
            $count = 0;
            foreach ($_COOKIE['viewedProd'] as $viewedProdId ){
                if($count < 4){
                    $viewedProd = get_post( $viewedProdId );
                    $img = get_the_post_thumbnail_url($viewedProd, 'full');
                    
                    if($img){
                        
                    }else{
                        $img = "https://apreal-nn.ru/wp-content/themes/apreal-nn/default-img.jpg";
                    }
                        
                    echo '<a href="'. get_permalink( $viewedProd->ID ) .'" class="recent__item">
                    <div class="recent__cont">
                        <img src="'. $img .'" class="recent__img" alt="">
                    </div>
                    <div class="recent__title">'. $viewedProd->post_title  .'</div>
                    </a>';
                    $count++;
                }else{
                    break;
                }
            }
		?>
		</div>
	</div>
<?php 
	}
?>
<!-- END Recent Posts -->

</div>

<?php
} // end while
} // end if
get_footer();
?>

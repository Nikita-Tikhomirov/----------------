<style>
	.tm-title-line:before, .tm-title-line:after {
		content: "";
		display: block;
		position: relative;
		width: 20%;
		height: 1px;
		background-color: #eaeaea;
		vertical-align: middle;
		margin: 0px 40px;
	}

	.tm-title-line:before {
	}
	#map{
		width: 65%;
		height: 400px;
	}
	.maped__cart h3{
		color: white;
		font-weight: 900;
	}
	.maped__cart h3:after{
    	display: block;
    	height: 10px;
    	margin-top: 10px;
    	background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAKAQMAAACZuXxsAAAABlBMV…AAACBJREFUCJlj4HASaGEQaFHkYFAEMhmAPAUGIM+BAZcEAMN3B/PbbjV8AAAAAElFTkSuQmCC) 0 0 repeat-x;
	}
	.maped__cart{
		width: 35%;
		padding-right: 25px;
	}
	.maped__cart ul{
		padding-left: 0px;
		list-style:none;
	}
	.maped__cart ul li{
		margin: 4px 0px;
	}
	.maped__cart ul li span:nth-child(1){
		font-weight: 900;
	}
	.maped__cart span{
		color: white;
		opacity: 1;
	}
	.maped__wrapper{
		    border-top: 1px solid #000;
    background: #2a2a2a;
    padding-top: 24px;
    padding-bottom: 24px;
	}
	.tm-uppercase{
		display: flex;
		justify-content: center;
		align-items: center;
		padding-top: 25px;
		margin-bottom: 20px;
		color: white;
	}
	.maped__cont{
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		max-width: 1200px;
		margin: 10px auto;
	}
	@media(max-width:992px){
		.maped__cart{
			width:100%;
		}
		#map{
			width: 100%;
			overflow: hidden;
		}
		.maped__cont{
			flex-wrap: wrap;
			padding: 20px;
		}
	}
</style>
<!--Footer-->
<div>
	<?php /* echo do_shortcode('[widgetkit id="16"]');*/ ?>
</div>

<!--Slider-->
<div class="footer-sld">
	<h3>
		Отзывы наших клиентов
	</h3>
	<div class="" uk-slider>

	<ul class="uk-slider-items uk-child-width-1-2@s uk-child-width-1-5@m uk-grid">
			<?php if( have_rows('reviews', 'option') ): ?>

				<?php while( have_rows('reviews', 'option') ): the_row(); ?>
					<li class="" uk-lightbox>
						<?php $img = get_sub_field('review_image'); ?>
						<a style="display:block;" href="<?php echo $img['url'] ?>"><img src="<?php echo $img['url'] ?>" alt="<?php echo $img['alt'] ?>" /></a>
					</li>
				<?php endwhile; ?>

			<?php endif; ?>
	</ul>

		<a href="#" class="uk-position-center-left uk-position-small uk-hidden-hover uk-icon uk-slidenav-previous uk-slidenav" uk-slider-item="previous">
		<svg version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
			 viewBox="0 0 477.175 477.175" style="enable-background:new 0 0 477.175 477.175;" xml:space="preserve">
		<g>
			<path d="M145.188,238.575l215.5-215.5c5.3-5.3,5.3-13.8,0-19.1s-13.8-5.3-19.1,0l-225.1,225.1c-5.3,5.3-5.3,13.8,0,19.1l225.1,225
				c2.6,2.6,6.1,4,9.5,4s6.9-1.3,9.5-4c5.3-5.3,5.3-13.8,0-19.1L145.188,238.575z"/>
		</g>
		</svg>
</a>
    <a href="#" class="uk-position-center-right uk-position-small uk-hidden-hover uk-icon uk-slidenav-next uk-slidenav" uk-slider-item="next">
		<svg version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
			 viewBox="0 0 477.175 477.175" style="enable-background:new 0 0 477.175 477.175;" xml:space="preserve">
		<g>
			<path d="M360.731,229.075l-225.1-225.1c-5.3-5.3-13.8-5.3-19.1,0s-5.3,13.8,0,19.1l215.5,215.5l-215.5,215.5
				c-5.3,5.3-5.3,13.8,0,19.1c2.6,2.6,6.1,4,9.5,4c3.4,0,6.9-1.3,9.5-4l225.1-225.1C365.931,242.875,365.931,234.275,360.731,229.075z
				"/>
		</g>
		</svg>
		</a>
	

	</div>
</div>

<!--Slider-->
<a href="#top" id="toTop"></a>
<footer class="footer">
	
	<div class="maped">
		<div class="maped__wrapper">
			
			<div class="tm-uppercase tm-title-line"> Группа Компаний 
				<img class="foot-logo uk-margin-small-left uk-margin-small-right ls-is-cached lazyloaded" src="https://www.apreal.ru/wp-content/uploads/2020/01/logotip3D100.png" data-src="https://www.apreal.ru/wp-content/uploads/2020/01/logotip3D100.png" alt="Demo" width="35" height="35">"АП-Риал"
			</div>
			
			<div class="maped__cont">
				<div class="maped__cart">
					<h3>
						Реквизиты компании:
					</h3>
					<ul>
						<li>
							<span>Полное наименование:</span>
							<span>Общество с ограниченной ответственностью «Группа компаний «АП-Риал»</span>
						</li>
						
						<li>
							<span>Юридический / Фактический адрес:</span>
							<span>107564, г. Москва, ул. Краснобогатырская, дом № 19 А</span>
						</li>
						
						<li>
							<span>ИНН:</span>
							<span>7709663385</span>
						</li>
						
						<li>
							<span>КПП:</span>
							<span>771801001</span>
						</li>
						
						<li>
							<span>ОГРН:</span>
							<span>1067746348713</span>
						</li>
						
						<li>
							<span>Телефоны:</span>
							<span>+7 495 137 54 58; +7 800 505 76 47</span>
						</li>
						
						<li>
							<span>Электронная почта:</span>
							<span>info@apreal.ru ; upreal@bk.ru</span>
						</li>
						
						<li>
							<span>Генеральный директор:</span>
							<span>Семенов Альберт Борисович </span>
						</li>
					</ul>
				</div>
					<div id="map"></div>
			</div>
			
			
			
		</div>
	</div>
	
    <div class="uk-container">
        <div class="uk-grid-collapse uk-child-width-expand@s uk-text-center" uk-grid>
        <div class="uk-width-1-4@m">
        </div>
        <div class="uk-width-expand@m">
            <div class="uk-padding uk-light">
            <p class="uk-text-meta">
                © Все права защищены 2006-<?php echo date("Y"); ?> г. Группа компаний "АП-Риал" www.apreal.ru
            </p>
			<a class="uk-text-meta" href="https://www.apreal.ru/konfedencialnost.html" target="_blank" rel="noopener noreferrer">
    Политика обработки персональных данных
  </a>
  | 
  <a class="uk-text-meta" href="/">
    Согласие на обработку ПД
  </a>	
            <hr>
            <p class="uk-text-meta">
                Группа компаний "АП-Риал": помощь в лицензировании всех видов деятельности. Обучение, предоставление оборудования для получения лицензий и разрешений.<br>
				<a title="карта сайта" target="_blank" rel="nofollow noopener" href="/map.htm">Карта сайта</a>
            </p>
            </div>
        </div>
        <div class="uk-width-1-4@m">
        </div>
        </div>
        
    </div>
<!-- Full Modal  -->

    <div id="modal-full" class="uk-modal-full" uk-modal>
        <div class="uk-modal-dialog">
            <button class="uk-modal-close-full uk-close-large" type="button" uk-close></button>
            <div class="uk-grid-collapse uk-child-width-1-2@s uk-flex-middle" uk-grid>
                <div class="uk-background-cover" style="background-image: url('/wp-content/themes/basic/img/modalBG.jpg');" uk-height-viewport></div>
                <div class="uk-padding-large">
                    <div style="color: #155296;font-size: 2.625rem;margin-top: 35px;">Оставить заявку</div>
                    
					<?php echo do_shortcode('[contact-form-7 id="1960" title="Оставить заявку"]'); ?>
				</div>
            </div>
        </div>
    </div>
<!-- ./Full Modal -->

<!-- Phone Back Modal -->

<div id="modal-sections" uk-modal>
    <div class="uk-modal-dialog">
        <button class="uk-modal-close-default" type="button" uk-close></button>
        <!-- <div class="uk-modal-header">
            <h2 class="uk-modal-title">Оставить заявку</h2>
        </div> -->
        <div class="uk-modal-body">
           <?php echo do_shortcode('[contact-form-7 id="4399" title="Контактная форма 1"]'); ?>
        </div>
        <div class="uk-modal-footer uk-text-right">
        </div>
    </div>
</div>
<!-- ./Phone Back Modal -->
	
<!-- Call Back Modal -->

<div id="cb-sections" uk-modal>
    <div class="uk-modal-dialog">
        <button class="uk-modal-close-default" type="button" uk-close></button>
        <!-- <div class="uk-modal-header">
            <h2 class="uk-modal-title">Оставить заявку</h2>
        </div> -->
        <div class="uk-modal-body">
<!--            <fieldset class="uk-fieldset">

				<legend class="uk-legend">Заказать звонок</legend>

				<div class="uk-margin">
				<input type="text" class="wpcf7-form-control wpcf7-text" style="display:block;width:0px;height:0px;opacity:0;padding:0px;margin:0px;">
					<input class="uk-input" type="text" id="f-name" name="f-name" required placeholder="Имя">
				</div>
				<div class="uk-margin masked-phone">
					<input class="uk-input" type="tel" id="cb-phone" name="f-phone" required placeholder="(___) ___-____">
				</div>
			   <p>
				   <span class="policity">Отправляя форму вы соглашаетесь с 
					   <a href="/konfedencialnost.html" target="_blank">политикой обработки персональных данных</a>					
				   </span>
			   </p>
			   <button class="uk-button uk-button-default" id="cb-send" type="submit" style="display:block;margin: 0 auto;">Отправить</button>
			</fieldset> -->
			<?php echo do_shortcode('[contact-form-7 id="6740" title="Заказать звонок"]'); ?>
        </div>
        <div class="uk-modal-footer uk-text-right">
        </div>
    </div>
</div>
<!-- ./Call Back Modal -->
	
</footer>
<?php wp_footer(); ?>
<div id="offcanvas-overlay" uk-offcanvas="overlay: true">
    <div class="uk-offcanvas-bar --mobile-menu-bar" style="background: #e2eff8;">

        <button class="uk-offcanvas-close" type="button" uk-close></button>

        <?php include( TEMPLATEPATH . '/sidebar-mobile.php'); ?>
        
    </div>
</div>
<script>
jQuery(document).ready(function(){
	jQuery('#primary-menu').append('<li><a href="#license-modal" role="button" style="color:red!important;" data-toggle="modal">Оставить заявку</a></li>');
	/* infogr */
stage=1;

	var intervalId_1=setInterval(function() {
		if(stage>3) stage=1; else stage++;
		showDetail(stage);
	}, 5000);

	function showDetail(number) {
		if(number==1) left=50;
		if(number==2) left=206;
		if(number==3) left=352;
		if(number==4) left=515;
		jQuery(".arrow").stop().animate({
			left: left,
		}, 200, function() {
		});
		jQuery(".info"+number).stop().animate({
			backgroundPosition: "(0 -64px)"
		}, 200, function() {
		});
		jQuery('.info-element').removeClass('act');
		jQuery('.info'+number).addClass('act');
		jQuery('.info-description').css('color', '#2e2e2e');
		jQuery('.desc'+number).css('color', 'red');
		jQuery('.info-texts').stop().fadeOut('fast');
		jQuery('.text'+number).stop().fadeIn('fast');
	}
	
	jQuery('.info1').mouseenter(function(){
		showDetail(1);
		clearInterval(intervalId_1);
	});
	jQuery('.info2').mouseenter(function(){
		showDetail(2);
		clearInterval(intervalId_1);
	});
	jQuery('.info3').mouseenter(function(){
		showDetail(3);
		clearInterval(intervalId_1);
	});
	jQuery('.info4').mouseenter(function(){
		showDetail(4);
		clearInterval(intervalId_1);
	});
	jQuery('.info-element').mouseout(function(){
		//jQuery('.arrow,.detail').hide();
		jQuery('.info-description').css('color', '#2e2e2e');
	});
	jQuery('.slider').mouseenter(function(){
		jQuery('#WP-ANYTHING-SETTING1').cycle('pause')
	});
	jQuery('.slider').mouseout(function(){
		jQuery('#WP-ANYTHING-SETTING1').cycle('resume')
	});
	
	function changeInfo(stageInfo) {
		if(stageInfo==1) slideTop='0';
		if(stageInfo==2) slideTop='121px';
		if(stageInfo==3) slideTop='242px';
		jQuery(".infographic-slide").stop().animate({
			top: slideTop,
		}, 500, function() {
		});
	}
	
	stageInfo=1;
	
	var intervalId_2=setInterval(function() {
		if(stageInfo>2) stageInfo=1; else stageInfo++;
		changeInfo(stageInfo);
	}, 3000);
	/* infogr */
	jQuery('.rcontact-header').mouseenter(function(){
		var current = jQuery('.content'+jQuery(this).attr('rel'));
		jQuery('.rcontact-content').slideUp(200);
		if(current.css('display')!='block') {
			current.slideDown(200);
		} else {
			current.slideUp(200);
		}
	});
	jQuery('#leftmenu aside h5').click(function(){
		var current = jQuery(this).siblings('div');
		jQuery('#leftmenu aside div').slideUp(200);
		if(current.css('display')!='block') {
			current.slideDown(200);
		} else  {
			current.slideUp(200);
		}
	});
	if(jQuery('.current-menu-item')) {
		jQuery('#leftmenu aside div').hide();
		jQuery('.current-menu-item').parent('ul').parent('div').show();
		jQuery('.current-menu-item').parent('ul').parent('li').parent('ul').parent('div').show();
		if(jQuery('.current-menu-item').parent('ul').attr('id')=='primary-menu') {
			jQuery('#leftmenu aside:first-child div').show();
		}
	}
	jQuery('.uk-button-danger').click(function(){
      console.log('click');
      jQuery('#urla').val(window.location.href);
		jQuery('#urla1').val(window.location.href);
    });
});</script>
<!-- <script src="https://api-maps.yandex.ru/2.1/?lang=ru-RU&amp;apikey=af311204-6179-49ee-a3fb-058a99c7dfc6" type="text/javascript"></script> -->
<script>
	setTimeout( () =>{
		 var d=document;

		var Sc = d.createElement('script'); 
		Sc.type = 'text/javascript'; 
		Sc.async = true;
		Sc.src = 'https://api-maps.yandex.ru/2.1/?lang=ru-RU&amp;apikey=af311204-6179-49ee-a3fb-058a99c7dfc6'; 
		var toPl = document.getElementsByTagName('script')[2]; 
		toPl.parentNode.insertBefore(Sc, toPl);

		setTimeout(() => {
			ymaps.ready(init);
		}, 5000);
	}, 6000);


function init () {
    var myMap = new ymaps.Map('map', {
            center: [55.76, 37.64],
            zoom: 4
        }, {
            searchControlProvider: 'yandex#search'
        }),
        objectManager = new ymaps.ObjectManager({
            // Чтобы метки начали кластеризоваться, выставляем опцию.
            clusterize: true,
            // ObjectManager принимает те же опции, что и кластеризатор.
            gridSize: 32,
            clusterDisableClickZoom: true
        });

    // Чтобы задать опции одиночным объектам и кластерам,
    // обратимся к дочерним коллекциям ObjectManager.
    objectManager.objects.options.set('preset', 'islands#greenDotIcon');
    objectManager.clusters.options.set('preset', 'islands#greenClusterIcons');
    myMap.geoObjects.add(objectManager);

	let data = {
    "type": "FeatureCollection",
    "features": [
       {"type": "Feature", "id": 0, "geometry": {"type": "Point", "coordinates": [55.812585, 37.698591]}, "properties": {"balloonContentHeader": "<font size=3><b>ГК АП-Риал</b></font>", "balloonContentBody": "в Москве (Главный офис)", "balloonContentFooter": "", "clusterCaption": "", "hintContent": ""}},
        {"type": "Feature", "id": 1, "geometry": {"type": "Point", "coordinates": [59.932996, 30.291712]}, "properties": {"balloonContentHeader": "<font size=3><b>ГК АП-Риал</b></font>", "balloonContentBody": "в Санкт-Петербурге", "balloonContentFooter": "", "clusterCaption": "", "hintContent": ""}},
        {"type": "Feature", "id": 2, "geometry": {"type": "Point", "coordinates": [45.072731, 39.009905]}, "properties": {"balloonContentHeader": "<font size=3><b>ГК АП-Риал</b></font>", "balloonContentBody": "в Краснодаре", "balloonContentFooter": "", "clusterCaption": "", "hintContent": ""}},
        {"type": "Feature", "id": 3, "geometry": {"type": "Point", "coordinates": [44.946150, 34.101269]}, "properties": {"balloonContentHeader": "<font size=3><b>ГК АП-Риал</b></font>", "balloonContentBody": "в Симферополе", "balloonContentFooter": "", "clusterCaption": "", "hintContent": ""}},
        {"type": "Feature", "id": 4, "geometry": {"type": "Point", "coordinates": [51.647359, 39.195993]}, "properties": {"balloonContentHeader": "<font size=3><b>ГК АП-Риал</b></font>", "balloonContentBody": "в Воронеже", "balloonContentFooter": "", "clusterCaption": "", "hintContent": ""}},
        {"type": "Feature", "id": 5, "geometry": {"type": "Point", "coordinates": [56.310582, 43.994740]}, "properties": {"balloonContentHeader": "<font size=3><b>ГК АП-Риал</b></font>", "balloonContentBody": "в Нижнем Новгороде", "balloonContentFooter": "", "clusterCaption": "", "hintContent": ""}},
        {"type": "Feature", "id": 6, "geometry": {"type": "Point", "coordinates": [54.720860, 20.499734]}, "properties": {"balloonContentHeader": "<font size=3><b>ГК АП-Риал</b></font>", "balloonContentBody": "в Калининграде", "balloonContentFooter": "", "clusterCaption": "", "hintContent": ""}},
        {"type": "Feature", "id": 7, "geometry": {"type": "Point", "coordinates": [57.147409, 65.544946]}, "properties": {"balloonContentHeader": "<font size=3><b>ГК АП-Риал</b></font>", "balloonContentBody": "в Тюмени", "balloonContentFooter": "", "clusterCaption": "", "hintContent": ""}},
        {"type": "Feature", "id": 8, "geometry": {"type": "Point", "coordinates": [48.729839, 44.524997]}, "properties": {"balloonContentHeader": "<font size=3><b>ГК АП-Риал</b></font>", "balloonContentBody": "в Волгограде", "balloonContentFooter": "", "clusterCaption": "", "hintContent": ""}},
        {"type": "Feature", "id": 8, "geometry": {"type": "Point", "coordinates": [53.238173, 50.245523]}, "properties": {"balloonContentHeader": "<font size=3><b>ГК АП-Риал</b></font>", "balloonContentBody": "в Самаре", "balloonContentFooter": "", "clusterCaption": "", "hintContent": ""}}
    
    ]
};
    objectManager.add(data);
}
</script>

<script>
// 	$("#cb-phone").inputmask({"mask": "(999) 999-9999"});
// 	setTimeout(()=> {
		
// 		document.querySelector('#cb-send').addEventListener('click', (e) => {
			
//         e.preventDefault();

//         let number = document.querySelector('#cb-phone').value;

//         jivo_api.startCall('+7' + number) 
//         document.querySelector('#cb-sections').click();

//         document.querySelector('#cb-phone').value = '';

//     });
// 	}, 11000);
</script>
<?php wp_footer(); ?>
</body>
</html>

<!--Footer-->
<footer class="footer">
	<div class="uk-container">
		<div class="uk-grid-collapse uk-child-width-expand@s uk-text-center" uk-grid>
			<div class="uk-width-1-4@m">
			</div>
			<div class="uk-width-expand@m">
				<div class="uk-padding uk-light">
					<p class="uk-text-meta">
						© Все права защищены 2006-<?php echo date("Y"); ?> г. Группа компаний "АП-Риал" www.apreal36.ru
					</p>
					<hr>
					<p class="uk-text-meta">
						Группа компаний "АП-Риал": консультирование и практическая помощь при создании и организации
						бизнеса старт-ап по заказу клиента в максимально короткие сроки с учетом индивидуальных
						особенностей.<br />
						<a title="карта сайта" target="_blank" rel="nofollow noopener" href="/sitemap">Карта сайта</a>
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
				<div class="uk-background-cover"
					style="background-image: url('/wp-content/themes/basic/img/modalBG.jpg');" uk-height-viewport></div>
				<div class="uk-padding-large">
					<div style="color: #155296;font-size: 2.625rem;margin-top: 35px;">Оставить заявку</div>
					<!-- <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p> -->
					<?php echo do_shortcode('[contact-form-7 id="1243" title="Оставить заявку"]'); ?>
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
				<?php echo do_shortcode('[contact-form-7 id="1242" title="Контактная форма 1"]'); ?>
			</div>
			<div class="uk-modal-footer uk-text-right">
				<!-- <button class="uk-button uk-button-default uk-modal-close" type="button">Cancel</button>
			<button class="uk-button uk-button-primary" type="button">Save</button> -->
			</div>
		</div>
	</div>
	<!-- ./Phone Back Modal -->
</footer>
<?php wp_footer(); ?>
<div id="offcanvas-overlay" uk-offcanvas="overlay: true">
	<div class="uk-offcanvas-bar --mobile-menu-bar" style="background: #e2eff8;">

		<button class="uk-offcanvas-close" type="button" uk-close></button>

		<?php include(TEMPLATEPATH . '/sidebar-mobile.php'); ?>

	</div>
</div>
<script>
	jQuery(document).ready(function () {
		jQuery('#primary-menu').append('<li><a href="#license-modal" role="button" style="color:red!important;" data-toggle="modal">Оставить заявку</a></li>');
		/* infogr */
		stage = 1;

		var intervalId_1 = setInterval(function () {
			if (stage > 3) stage = 1; else stage++;
			showDetail(stage);
		}, 5000);

		function showDetail(number) {
			if (number == 1) left = 50;
			if (number == 2) left = 206;
			if (number == 3) left = 352;
			if (number == 4) left = 515;
			jQuery(".arrow").stop().animate({
				left: left,
			}, 200, function () {
			});
			jQuery(".info" + number).stop().animate({
				backgroundPosition: "(0 -64px)"
			}, 200, function () {
			});
			jQuery('.info-element').removeClass('act');
			jQuery('.info' + number).addClass('act');
			jQuery('.info-description').css('color', '#2e2e2e');
			jQuery('.desc' + number).css('color', 'red');
			jQuery('.info-texts').stop().fadeOut('fast');
			jQuery('.text' + number).stop().fadeIn('fast');
		}

		jQuery('.info1').mouseenter(function () {
			showDetail(1);
			clearInterval(intervalId_1);
		});
		jQuery('.info2').mouseenter(function () {
			showDetail(2);
			clearInterval(intervalId_1);
		});
		jQuery('.info3').mouseenter(function () {
			showDetail(3);
			clearInterval(intervalId_1);
		});
		jQuery('.info4').mouseenter(function () {
			showDetail(4);
			clearInterval(intervalId_1);
		});
		jQuery('.info-element').mouseout(function () {
			//jQuery('.arrow,.detail').hide();
			jQuery('.info-description').css('color', '#2e2e2e');
		});
		jQuery('.slider').mouseenter(function () {
			jQuery('#WP-ANYTHING-SETTING1').cycle('pause')
		});
		jQuery('.slider').mouseout(function () {
			jQuery('#WP-ANYTHING-SETTING1').cycle('resume')
		});

		function changeInfo(stageInfo) {
			if (stageInfo == 1) slideTop = '0';
			if (stageInfo == 2) slideTop = '121px';
			if (stageInfo == 3) slideTop = '242px';
			jQuery(".infographic-slide").stop().animate({
				top: slideTop,
			}, 500, function () {
			});
		}

		stageInfo = 1;

		var intervalId_2 = setInterval(function () {
			if (stageInfo > 2) stageInfo = 1; else stageInfo++;
			changeInfo(stageInfo);
		}, 3000);
		/* infogr */
		jQuery('.rcontact-header').mouseenter(function () {
			var current = jQuery('.content' + jQuery(this).attr('rel'));
			jQuery('.rcontact-content').slideUp(200);
			if (current.css('display') != 'block') {
				current.slideDown(200);
			} else {
				current.slideUp(200);
			}
		});
		jQuery('#leftmenu aside h5').click(function () {
			var current = jQuery(this).siblings('div');
			jQuery('#leftmenu aside div').slideUp(200);
			if (current.css('display') != 'block') {
				current.slideDown(200);
			} else {
				current.slideUp(200);
			}
		});
		if (jQuery('.current-menu-item')) {
			jQuery('#leftmenu aside div').hide();
			jQuery('.current-menu-item').parent('ul').parent('div').show();
			jQuery('.current-menu-item').parent('ul').parent('li').parent('ul').parent('div').show();
			if (jQuery('.current-menu-item').parent('ul').attr('id') == 'primary-menu') {
				jQuery('#leftmenu aside:first-child div').show();
			}
		}

		jQuery('.uk-button-danger').click(function () {
			jQuery('#urla').val(window.location.href);
			jQuery('#urla1').val(window.location.href);
		});
	});</script>








<!-- Попап фон -->
<div class="unipop-overlay" id="unipop-overlay"></div>

<!-- === Попап 1: ЗАКАЗАТЬ ЗВОНОК === -->
<div class="unipop" id="popup-callback">
	<div class="unipop-inner">
		<button class="unipop-close">&times;</button>
		<h2 class="unipop-title">ЗАКАЗАТЬ ЗВОНОК</h2>

		<form class="unipop-form" data-form="callback">
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

		<form class="unipop-form" data-form="question">
			<input type="email" name="email" required placeholder="mail@example.com">
			<textarea name="coment" placeholder="Вопрос" id=""></textarea>
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
		const buttons = document.querySelectorAll('button.uk-button.uk-button-danger[href="#modal-sections"]');

		buttons.forEach(button => {
			// Создаем новый div
			const newButton = document.createElement('div');
			newButton.classList.add('uk-button', 'uk-button-danger', 'open-question');
			newButton.style.fontSize = '14px';
			newButton.style.paddingLeft = '0px';
			newButton.style.paddingRight = '0px';
			newButton.style.width = '100%';

			// Копируем атрибут style
			newButton.setAttribute('style', button.getAttribute('style'));

			// Создаем span
			const span = document.createElement('span');
			span.classList.add('uk-button-danger__inner');
			span.textContent = 'ЗАДАТЬ ВОПРОС';

			// Вставляем span в div
			newButton.appendChild(span);

			button.parentNode.replaceChild(newButton, button);
		});

		const overlay = document.getElementById('unipop-overlay');
		const popups = document.querySelectorAll('.unipop');

		// --- Открытие ---
		function openPopup(id) {
			overlay.classList.add('active');
			document.getElementById(id).classList.add('active');
			document.documentElement.classList.add('unipop-open');
		}

		// --- Закрытие ---
		function closePopup() {
			overlay.classList.remove('active');
			popups.forEach(p => p.classList.remove('active'));
			document.documentElement.classList.remove('unipop-open');
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
		document.querySelectorAll('.unipop-form').forEach(form => {
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
	html.unipop-open body > jdiv {
		display: none !important;
	}

	.unipop-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.6);
		display: none;
		z-index: 999;
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
		z-index: 1000;
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
		color: #155296;
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
		min-height: 40px;
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

	/* .uk-button-danger:hover:before {
		z-index: 0 !important;
	} */
		.uk-article table .uk-button{
			padding-left: 5px;
			padding-right: 5px;
			margin: auto;
			display: block;
		}
		.uk-article table .uk-button span{
			white-space: nowrap;
		}

		.uk-article .uk-button {
			display: block;
			margin: auto;
			width: fit-content;
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

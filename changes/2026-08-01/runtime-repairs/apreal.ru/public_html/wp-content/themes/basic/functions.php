<?php
$themeDIR = '/wp-content/themes/basic';

remove_filter( 'the_content', 'wpautop' );
/**
 * Include CSS files
 */
function theme_enqueue_scripts() {
        wp_enqueue_style( 'UIkit', get_template_directory_uri() . '/css/uikit.min.css' );
        wp_enqueue_style(
                'Style',
                get_template_directory_uri() . '/style.css',
                array(),
                filemtime(get_template_directory() . '/style.css')
        );
	
         wp_enqueue_script( 'jQuery', 'https://code.jquery.com/jquery-3.4.1.min.js', array(), '3.4.1', true );
		 wp_enqueue_script( 'maski', get_template_directory_uri() . '/js/jquery.inputmask.min.js', array(), '1.0.1', true );
		
        // 
        wp_enqueue_script( 'UIkitjs', get_template_directory_uri() . '/js/uikit.min.js', array(), '1.0.0', true );
        wp_enqueue_script( 'UIicons', get_template_directory_uri() . '/js/uikit-icons.min.js', array(), '1.0.0', true );

        }
add_action( 'wp_enqueue_scripts', 'theme_enqueue_scripts' );

//add_filter('show_admin_bar', '__return_false'); // отключить

## делает IMG тег анкором ссылки на картинку указанную в этом теге, чтобы её можно было увеличить и посмотреть.
add_filter( 'the_content', function( $content ){
	//$content .= 'qq';
	// пропускаем если в тексте нет картинок вообще...
	if( false === strpos( $content, '<img ') )
	  return $content;
  
	// if( ! is_main_query() || ! in_array( $GLOBALS['post']->post_type, ['post'] ) )
	//   return $content;
	$oo = null;
	$img_ex = '<img[^>]*src *= *["\']([^\'"]+)["\'][^>]*>';
	$content = preg_replace_callback( "~(?:<a[^>]+>\s*)$img_ex|($img_ex)~", function($mm){
	  // пропускаем, если картинка уже со ссылкой
	  if( empty($mm[2]) )
		return $mm[0];
		
			$align = '';
		if (strpos($mm[2], 'alignright') !== false) {
			$align = 'alignright';
		}elseif(strpos($mm[2], 'alignleft') !== false){
			$align = 'alignleft';
		}
	  return '<span class="'.$align.'" uk-lightbox><a href="'. $mm[3] .'" class="uk-inline">'. $mm[2] .'</a></span>';
	  //'<div>' . $mm[0] . '<br>' . $mm[1] . '<br>' . $mm[2] . '<br>' . $mm[3] . '</div>';
	}, $content );
	print_r($oo);
	
	return $content;
  }, 65 );

/**
 * Setup Theme
 */
function mdbtheme_setup() {
    // Add featured image support
    add_theme_support('post-thumbnails');
}
add_action('after_setup_theme', 'mdbtheme_setup');
/**
 * Include external files
 */
// include_once(__DIR__ .'/inc/pagination.inc.php');
// include_once(__DIR__ .'/inc/template-tags.inc.php');
/**
 * Register our sidebars and widgetized areas.
 */
function mdb_widgets_init() {

    register_sidebar( array(
      'name'          => 'Sidebar',
      'id'            => 'sidebar',
      'before_widget' => '',
      'after_widget'  => '',
      'before_title'  => '',
      'after_title'   => '',
    ) );
  
  }
  add_action( 'widgets_init', 'mdb_widgets_init' );
//Custom pagination
function mdb_pagination() {
if( is_singular() )
return;
global $wp_query;
/** Stop execution if there's only 1 page */
if( $wp_query->max_num_pages <= 1 )
return;
$paged = get_query_var( 'paged' ) ? absint( get_query_var( 'paged' ) ) : 1;
$max   = intval( $wp_query->max_num_pages );
/** Add current page to the array */
if ( $paged >= 1 )
$links[] = $paged;
/** Add the pages around the current page to the array */
if ( $paged >= 3 ) {
$links[] = $paged - 1;
$links[] = $paged - 2;
}
if ( ( $paged + 2 ) <= $max ) {
$links[] = $paged + 2;
$links[] = $paged + 1;
}
echo '<nav id="mdb-navigation" class="d-flex justify-content-center my-4 wow fadeIn">' . "\n";
  echo '<ul class="pagination pagination-circle pg-info mb-0">' . "\n";
    /** Previous Post Link */
    if ( get_previous_posts_link() )
    printf( ' <li>%s</li>
    ' . "\n", get_previous_posts_link('<span aria-hidden="true">&laquo;</span>
    <span class="sr-only">Previous</span>
    ') );
    /** Link to first page, plus ellipses if necessary */
    if ( ! in_array( 1, $links ) ) {
    $class = 1 == $paged ? ' class="active"' : '';
    printf( '<li%s><a href="%s">%s</a></li>' . "\n", $class, esc_url( get_pagenum_link( 1 ) ), '1' );
    if ( ! in_array( 2, $links ) )
    echo '<li>…</li>';
    }
    /** Link to current page, plus 2 pages in either direction if necessary */
    sort( $links );
    foreach ( (array) $links as $link ) {
    $class = $paged == $link ? ' class="active"' : '';
    printf( '<li%s><a href="%s">%s</a></li>' . "\n", $class, esc_url( get_pagenum_link( $link ) ), $link );
    }
    /** Link to last page, plus ellipses if necessary */
    if ( ! in_array( $max, $links ) ) {
    if ( ! in_array( $max - 1, $links ) )
    echo '<li>…</li>' . "\n";
    $class = $paged == $max ? ' class="active"' : '';
    printf( '<li%s><a href="%s">%s</a></li>' . "\n", $class, esc_url( get_pagenum_link( $max ) ), $max );
    }
    /** Next Post Link */
    if ( get_next_posts_link() )
    printf( '<li>%s</li>
    ' . "\n", get_next_posts_link('<span aria-hidden="true">&raquo;</span>
    <span class="sr-only">Next</span>') );
  echo '</ul>' . "\n";
echo '</nav>' . "\n";
echo '<!--/.Pagination-->' . "\n";
}

/**
 * Check if post is in a menu
 *
 * @param $menu menu name, id, or slug
 * @param $object_id int post object id of page
 * @return bool true if object is in menu
 */
function cms_is_in_menu( $menu = null, $object_id = null ) {

    // get menu object
    $menu_object = wp_get_nav_menu_items( esc_attr( $menu ) );

    // stop if there isn't a menu
    if( ! $menu_object )
        return false;

    // get the object_id field out of the menu object
    $menu_items = wp_list_pluck( $menu_object, 'object_id' );

    // use the current post if object_id is not specified
    if( !$object_id ) {
        global $post;
        $object_id = get_queried_object_id();
    }

    // test if the specified page is in the menu or not. return true or false.
    return in_array( (int) $object_id, $menu_items );

}

add_shortcode( 'callback', 'mytag_func' );
function mytag_func( $atts, $content ) {
	$a = shortcode_atts( array(
      'goal' => 'callback'
   ), $atts );
	 return '<button onclick="ym(\'6385843\', \'reachGoal\', \''. $atts['goal']  .'\'); return true;" class="uk-button uk-button-danger phones__callback" href="#modal-sections" uk-toggle=""><span class="uk-button-danger__inner">'. $content .'</span></button>';
}

function remove_gutenberg_styles() {
	wp_dequeue_style( 'wp-block-library' );
}

add_action( 'wp_enqueue_scripts', 'remove_gutenberg_styles', 100 );

if( function_exists('acf_add_options_page') ) {
	
	acf_add_options_page(array(
		'page_title' 	=> 'Основные настройки',
		'menu_title'	=> 'Настройки темы',
		'menu_slug' 	=> 'theme-general-settings',
		'capability'	=> 'edit_posts',
		'redirect'		=> false
	));
	
	acf_add_options_sub_page(array(
		'page_title' 	=> 'Настройки шапки',
		'menu_title'	=> 'Шапка',
		'parent_slug'	=> 'theme-general-settings',
	));
	
	acf_add_options_sub_page(array(
		'page_title' 	=> 'Настройки подвала',
		'menu_title'	=> 'Подвал',
		'parent_slug'	=> 'theme-general-settings',
	));
	
}

// Колонка миниатюры в списке записей админки
add_filter('manage_posts_columns', 'posts_columns', 5);
add_action('manage_posts_custom_column', 'posts_custom_columns', 5, 2);
 
function posts_columns($defaults){
    $defaults['riv_post_thumbs'] = __('Миниатюра');
    return $defaults;
}
 
function posts_custom_columns($column_name, $id){
 if($column_name === 'riv_post_thumbs'){
        the_post_thumbnail( array(50, 50) );
    }
}

// TAbles
add_shortcode( 'table-prices', 'table_prices' );
function table_prices(  ) {
	 return ' <table class="licenses">
    <thead>
       <tr>
           <th>Лицензия</th>
           <th>Стоимость</th>
           <th>Сроки</th>
       </tr>
   </thead>
   <tbody>
       <tr>
           <td><a href="http://www.apreal.ru/licenzija_mchs.html" target="_blank" rel="nofollow noopener noreferrer" title="Лицензия МЧС">Лицензия МЧС</a> (на все виды деятельности)</td>
           <td>70-130 тыс. рублей</td>
           <td>до 45 рабочих дней</td>
       </tr>
       <tr>
           <td><a href="http://www.apreal.ru/mchs/pereoformlenie.html" target="_blank" rel="nofollow noopener noreferrer" title="Переоформление лицензии">Переоформление лицензии</a></td>
           <td>60-120 тыс. рублей</td>
           <td>до 30 рабочих дней</td>
       </tr>
       <tr>
           <td><a href="http://www.apreal.ru/mchs/arenda-oborudovaniya-mchs.html" target="_blank" title="Аренда оборудования для пожарной лицензии" rel="nofollow noopener noreferrer">Аренда оборудования для пожарной лицензии</a></td>
           <td>от 20 000 рублей</td>
           <td>3 дня</td>
       </tr>
       <tr>
           <td><a href="http://www.apreal.ru/mchs/obuchenie.html" target="_blank" title="Обучение для лицензирования" rel="nofollow noopener noreferrer">Обучение для лицензирования</a></td>
           <td>4 000 рублей</td>
           <td>72 академических часа </td>
       </tr>
       <tr>
           <td><a href="http://www.apreal.ru/liccontrol.html" target="_blank" title="Лицензионный контроль под ключ" rel="noopener noreferrer">Лицензионный контроль под ключ</a></td>
           <td>от 20 000 рублей</td>
           <td>1 неделя</td>
       </tr>
       <tr>
           <td><a href="http://www.apreal.ru/baza-pb.html" target="_blank" rel="nofollow noopener noreferrer" title="Диск с нормативной документацией">Диск с нормативной документацией</a></td>
           <td>6 000 рублей</td>
           <td>1 день</td>
       </tr>
       <tr>
           <td><a href="http://www.apreal.ru/kontrol-kachestva.html" target="_blank" title="Система контроля качества по ПБ" rel="nofollow noopener noreferrer">Система контроля качества по ПБ</a></td>
           <td>от 20 000 рублей</td>
           <td>3 дня</td>
       </tr>
   </tbody>
</table>';
}
// Tables
// 
// 
// TAbles
add_shortcode( 'table-othodi', 'table_othodi' );
function table_othodi(  ) {
	 return '<noindex> <table class="licenses">
    <thead>
       <tr>
           <th>Класс отходности</th>
           <th>Примеры материалов/веществ/товаров</th>
       </tr>
   </thead>
   <tbody>
       <tr>
           <td>1.&nbsp;Чрезвычайно опасные</td>
           <td>Дифенильные вещества, терфенилы, трансформаторы, конденсаторы, антидетонационые присадки, крезол, минеральные масла и масла из синтетики.</td>
       </tr>
       <tr>
           <td>2.&nbsp;Высокоопасные</td>
           <td>Освинцованный кабель, свинцовые аккумуляторы, отходы нефтепродуктов после процесса рафинирования, щелочи и кислота от аккумуляторов, отходы свинцовых солей и медного хлорида в твердом состоянии, свинцовые опилки.</td>
       </tr>
       <tr>
           <td>3.&nbsp;Умеренно опасные</td>
           <td>Ацетон, материал обтирки, очистной шлам нефтепроводов и нефтяных емкостей, дизельное топливо, моторные масла, грязный песок, пыль от цемента, помет уток, кур, гусей, свиной навоз.</td>
       </tr>
       <tr>
           <td>4.&nbsp;Малоопасные</td>
           <td>Мусор от строительства, бытовой мусор, не подвергшийся сортированию, покрышки, битумные, асфальтные отходы, черно металлическая пыль, картонные и бумажные остатки, рубероид, перьевые остатки, навоз.   </td>
       </tr>
       <tr>
           <td>5.&nbsp;Практически не опасные</td>
           <td>Скорлупа, стружка от дерева, упаковка из древесины, зола, предметы из керамики, обломки кирпича, отходы пищи.</td>
       </tr>
       
   </tbody>
</table>
</noindex>';
}
// Tables
// 
// 
// TAbles
add_shortcode( 'table-othodi-uslugi', 'table_othodi_uslugi' );
function table_othodi_uslugi(  ) {
	 return ' <table class="licenses">
    <thead>
       <tr>
           <th>Лицензия</th>
           <th>Стоимость</th>
		   <th>Сроки</th>
       </tr>
   </thead>
   <tbody>
       <tr>
           <td><a href="http://www.apreal.ru/rtnadzor-obra.htm" target="_blank" rel="nofollow noopener noreferrer" title="Лицензия на отходы под ключ">Лицензия на отходы под ключ</a></td>
		   <td>250-700 тыс. рублей</td>
           <td>до 45 рабочих дней</td>
       </tr>
	   
	   <tr>
           <td>Переоформление лицензии</td>
		   <td>250-500 тыс. рублей</td>
           <td>до 30 рабочих дней</td>
       </tr>
	   
	   <tr>
           <td><a href="http://www.apreal.ru/othodi/obuchenie-ecologiya.html" target="_blank" rel="nofollow noopener noreferrer" title="Обучение по экологической безопасности">Обучение для лицензирования</a></td>
		   <td>4 000 рублей</td>
           <td>72 академических часа </td>
       </tr>
	   
	   <tr>
           <td><a href="http://www.apreal.ru/othodi/sanitarnoe-zakluchenie.html" target="_blank" rel="nofollow noopener noreferrer" title="Оформление санитарного и экспертного заключения">Оформление санитарного и экспертного заключения</a></td>
		   <td>от 100 000 рублей</td>
           <td>до 30 рабочих дней</td>
       </tr>
	   
	   <tr>
           <td><a href="http://www.apreal.ru/othodi/ekologia-programma.html" target="_blank" title="Производственный экологический контроль" rel="noopener">Производственный экологический контроль</a></td>
		   <td>50 000 рублей</td>
           <td>5 дней</td>
       </tr>
	   
	   <tr>
           <td>Договор на дезинфекцию, дезинсекцию, дератизацию</td>
		   <td>10 000 рублей</td>
           <td>5 дней</td>
       </tr>
	   
	   <tr>
           <td>Поиск транспорта и площадки</td>
		   <td>80 000 рублей</td>
           <td>5-7 дней</td>
       </tr>
       
   </tbody>
</table>';
}
// Tables
?>

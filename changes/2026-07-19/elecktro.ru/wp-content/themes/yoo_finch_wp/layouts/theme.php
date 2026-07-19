<?php
/**
* @package   Finch
* @author    YOOtheme http://www.yootheme.com
* @copyright Copyright (C) YOOtheme GmbH
* @license   http://www.gnu.org/licenses/gpl.html GNU/GPL
*/

// get theme configuration
include($this['path']->path('layouts:theme.config.php'));

?>
<!DOCTYPE HTML>
<html lang="<?php echo $this['config']->get('language'); ?>" dir="<?php echo $this['config']->get('direction'); ?>"  data-config='<?php echo $this['config']->get('body_config','{}'); ?>'>

<head>
<?php echo $this['template']->render('head'); ?>
</head>

<body class="<?php echo $this['config']->get('body_classes'); ?>">

    <?php if ($this['widgets']->count('socialbar')) : ?>
    <div class="tm-socialbar uk-hidden-small">
        <?php echo $this['widgets']->render('socialbar'); ?>
    </div>
    <?php endif; ?>

    <?php if ($this['widgets']->count('toolbar-l + toolbar-r')) : ?>
    <div class="tm-toolbar uk-clearfix uk-visible-large">

        <?php if ($this['widgets']->count('toolbar-l')) : ?>
        <div class="uk-float-left"><?php echo $this['widgets']->render('toolbar-l'); ?></div>
        <?php endif; ?>

        <?php if ($this['widgets']->count('toolbar-r')) : ?>
        <div class="uk-float-right"><?php echo $this['widgets']->render('toolbar-r'); ?></div>
        <?php endif; ?>

    </div>
    <?php endif; ?>

    <?php if ($this['widgets']->count('logo + menu + search')) : ?>

    <?php if ($this['config']->get('navbar_mode')) : ?>
    <div <?php echo $sticky; ?>>
    <?php endif; ?>

        <nav class="tm-navbar uk-navbar <?php echo $navbar; ?>">

            <?php if ($this['widgets']->count('logo')) : ?>
            <a class="tm-logo uk-float-left uk-visible-large" href="<?php echo $this['config']->get('site_url'); ?>"><?php echo $this['widgets']->render('logo'); ?></a>
            <?php endif; ?>

            <?php if ($this['widgets']->count('menu')) : ?>
            <?php echo $this['widgets']->render('menu'); ?>
            <?php endif; ?>

            <?php if ($this['widgets']->count('offcanvas')) : ?>
            <a href="#offcanvas" class="uk-navbar-toggle uk-hidden-large" data-uk-offcanvas></a>
            <?php endif; ?>

            <?php if ($this['widgets']->count('search + menu-button')) : ?>
            <div class="uk-navbar-flip">
            <?php if ($this['widgets']->count('search')) : ?>
                <div class="uk-navbar-content uk-visible-large"><?php echo $this['widgets']->render('search'); ?></div>
            <?php endif; ?>
            <?php if ($this['widgets']->count('menu-button')) : $menu_button = $this['widgets']->load('menu-button')?>
               <div class="uk-flex uk-flex-middle uk-navbar-content tm-menu-button uk-visible-large">
                   <a class="uk-button eModal-1" href="#"><?php echo $menu_button[0]->title; ?></a>
               </div>
            <?php endif; ?>
            </div>
            <?php endif; ?>

            <?php if ($this['widgets']->count('logo-small')) : ?>
            <div class="uk-navbar-content uk-navbar-center uk-hidden-large"><a class="tm-logo-small" href="<?php echo $this['config']->get('site_url'); ?>"><?php echo $this['widgets']->render('logo-small'); ?></a></div>
            <?php endif; ?>

        </nav>

    <?php if ($this['config']->get('navbar_mode')) : ?>
    </div>
    <?php endif; ?>

    <?php endif; ?>

   <?php if ($this['widgets']->count('top-a')) : ?>
   <div id="tm-top-a" class="uk-block tm-block-top-a <?php echo @$block_classes['top-a']; echo @$display_classes['top-a']; ?>" <?php echo $styles['block.top-a']; ?>>
        <div class="uk-container uk-container-center">

            <section class="<?php echo $grid_classes['top-a']; echo @$display_classes['top-a']; ?>" data-uk-grid-match="{target:'> div > .uk-panel'}" data-uk-grid-margin>
                <?php echo $this['widgets']->render('top-a', array('layout'=>$this['config']->get('grid.top-a.layout'))); ?>
            </section>

        </div>
    </div>
    <?php endif; ?>

    <?php if ($this['widgets']->count('top-b')) : ?>
        <div id="tm-top-b" class="uk-block tm-block-top-b <?php echo @$block_classes['top-b']; echo @$display_classes['top-b']; ?>" <?php echo $styles['block.top-b']; ?>>
             <div class="uk-container uk-container-center">

                 <section class="<?php echo $grid_classes['top-b']; echo @$display_classes['top-b']; ?>" data-uk-grid-match="{target:'> div > .uk-panel'}" data-uk-grid-margin>
                     <?php echo $this['widgets']->render('top-b', array('layout'=>$this['config']->get('grid.top-b.layout'))); ?>
                 </section>

             </div>
         </div>
    <?php endif; ?>

    <?php if ($this['widgets']->count('top-c')) : ?>
        <div id="tm-top-c" class="uk-block tm-block-top-c <?php echo @$block_classes['top-c']; echo @$display_classes['top-c']; ?>" <?php echo $styles['block.top-c']; ?>>
             <div class="uk-container uk-container-center">

                 <section class="<?php echo $grid_classes['top-c']; echo @$display_classes['top-c']; ?>" data-uk-grid-match="{target:'> div > .uk-panel'}" data-uk-grid-margin>
                     <?php echo $this['widgets']->render('top-c', array('layout'=>$this['config']->get('grid.top-c.layout'))); ?>
                 </section>

             </div>
         </div>
    <?php endif; ?>

   <?php if ($this['widgets']->count('top-d')) : ?>
       <div id="tm-top-d" class="uk-block tm-block-top-d <?php echo @$block_classes['top-d']; echo @$display_classes['top-d']; ?>" <?php echo $styles['block.top-d']; ?>>
            <div class="uk-container uk-container-center">

                <section class="<?php echo $grid_classes['top-d']; echo @$display_classes['top-d']; ?>" data-uk-grid-match="{target:'> div > .uk-panel'}" data-uk-grid-margin>
                    <?php echo $this['widgets']->render('top-d', array('layout'=>$this['config']->get('grid.top-d.layout'))); ?>
                </section>

            </div>
        </div>
    <?php endif; ?>

    <?php if ($this['widgets']->count('main-top + main-bottom + sidebar-a + sidebar-b') || $this['config']->get('system_output', true)) : ?>
    <div id="tm-main" class="uk-block tm-block-main <?php echo $block_classes['main']; ?>" <?php echo $styles['block.main']; ?> >

        <div class="uk-container uk-container-center">

            <div class="tm-middle uk-grid" data-uk-grid-match data-uk-grid-margin>

                <?php if ($this['widgets']->count('main-top + main-bottom') || $this['config']->get('system_output', true)) : ?>
                <div class="<?php echo $columns['main']['class'] ?>">

                    <?php if ($this['widgets']->count('main-top')) : ?>
                    <section id="tm-main-top" class="<?php echo $grid_classes['main-top']; echo @$display_classes['main-top']; ?>" data-uk-grid-match="{target:'> div > .uk-panel'}" data-uk-grid-margin><?php echo $this['widgets']->render('main-top', array('layout'=>$this['config']->get('grid.main-top.layout'))); ?></section>
                    <?php endif; ?>

                    <?php if ($this['config']->get('system_output', true)) : ?>
                    <main id="tm-content" class="tm-content">

                        <?php if ($this['widgets']->count('breadcrumbs')) : ?>
                        <?php echo $this['widgets']->render('breadcrumbs'); ?>
                        <?php endif; ?>

                        <?php echo $this['template']->render('content'); ?>

                    </main>
                    <?php endif; ?>

                    <?php if ($this['widgets']->count('main-bottom')) : ?>
                    <section id="tm-main-bottom" class="<?php echo $grid_classes['main-bottom']; echo @$display_classes['main-bottom']; ?>" data-uk-grid-match="{target:'> div > .uk-panel'}" data-uk-grid-margin><?php echo $this['widgets']->render('main-bottom', array('layout'=>$this['config']->get('grid.main-bottom.layout'))); ?></section>
                    <?php endif; ?>

                </div>
                <?php endif; ?>

                <?php foreach($columns as $name => &$column) : ?>
                <?php if ($name != 'main' && $this['widgets']->count($name)) : ?>
                <aside class="<?php echo $column['class'] ?>"><?php echo $this['widgets']->render($name) ?></aside>
                <?php endif ?>
                <?php endforeach ?>

            </div>

        </div>

    </div>
    <?php endif; ?>

    <?php if ($this['widgets']->count('bottom-a')) : ?>
    <div id="tm-bottom-a" class="uk-block tm-block-bottom-a <?php echo @$block_classes['bottom-a']; echo @$display_classes['bottom-a']; ?>" <?php echo $styles['block.bottom-a']; ?>>

        <div class="uk-container uk-container-center">

            <section class="<?php echo $grid_classes['bottom-a']; echo @$display_classes['bottom-a']; ?>" data-uk-grid-match="{target:'> div > .uk-panel'}" data-uk-grid-margin>
                <?php echo $this['widgets']->render('bottom-a', array('layout'=>$this['config']->get('grid.bottom-a.layout'))); ?>
            </section>

        </div>

    </div>
    <?php endif; ?>

    <?php if ($this['widgets']->count('bottom-b')) : ?>
        <div id="tm-bottom-b" class="uk-block tm-block-bottom-b <?php echo @$block_classes['bottom-b']; echo @$display_classes['bottom-b']; ?>" <?php echo $styles['block.bottom-b']; ?>>

            <div class="uk-container uk-container-center">

                <section class="<?php echo $grid_classes['bottom-b']; echo @$display_classes['bottom-b']; ?>" data-uk-grid-match="{target:'> div > .uk-panel'}" data-uk-grid-margin>
                    <?php echo $this['widgets']->render('bottom-b', array('layout'=>$this['config']->get('grid.bottom-b.layout'))); ?>
                </section>

            </div>

        </div>
    <?php endif; ?>

    <?php if ($this['widgets']->count('bottom-c')) : ?>
        <div id="tm-bottom-c" class="uk-block tm-block-bottom-c <?php echo @$block_classes['bottom-c']; echo @$display_classes['bottom-c']; ?>" <?php echo $styles['block.bottom-c']; ?>>

            <div class="uk-container uk-container-center">

                <section class="<?php echo $grid_classes['bottom-c']; echo @$display_classes['bottom-c']; ?>" data-uk-grid-match="{target:'> div > .uk-panel'}" data-uk-grid-margin>
                    <?php echo $this['widgets']->render('bottom-c', array('layout'=>$this['config']->get('grid.bottom-c.layout'))); ?>
                </section>

            </div>

        </div>
    <?php endif; ?>

    <?php if ($this['widgets']->count('bottom-d')) : ?>
        <div id="tm-bottom-d" class="uk-block tm-block-bottom-d <?php echo @$block_classes['bottom-d']; echo @$display_classes['bottom-d']; ?>" <?php echo $styles['block.bottom-d']; ?>>

            <div class="uk-container uk-container-center">

                <section class="<?php echo $grid_classes['bottom-d']; echo @$display_classes['bottom-d']; ?>" data-uk-grid-match="{target:'> div > .uk-panel'}" data-uk-grid-margin>
                    <?php echo $this['widgets']->render('bottom-d', array('layout'=>$this['config']->get('grid.bottom-d.layout'))); ?>
                </section>

            </div>

        </div>
    <?php endif; ?>

    <?php if ($this['widgets']->count('footer + debug') || $this['config']->get('warp_branding', true) || $this['config']->get('totop_scroller', true)) : ?>
    <div id="tm-footer" class="uk-block tm-block-footer <?php echo @$block_classes['footer']; echo @$display_classes['footer']; ?>" <?php echo $styles['block.footer']; ?>>
        <div class="uk-container uk-container-center">

            <footer class="tm-footer">

                <?php
                    echo $this['widgets']->render('footer');
                    $this->output('warp_branding');
                    echo $this['widgets']->render('debug');
                ?>

                <?php if ($this['config']->get('totop_scroller', true)) : ?>
                <a class="tm-totop-scroller" data-uk-smooth-scroll href="#"></a>
                <?php endif; ?>

            </footer>

        </div>
    </div>
    <?php endif; ?>

    <?php echo $this->render('footer'); ?>

    <?php if ($this['widgets']->count('offcanvas')) : ?>
    <div id="offcanvas" class="uk-offcanvas">
        <div class="uk-offcanvas-bar"><?php echo $this['widgets']->render('offcanvas'); ?></div>
    </div>
    <?php endif; ?>

<script src="//code-ru1.jivosite.com/widget.js" jv-id="Fmn8JX3Co4" async></script>

<!-- Yandex.Metrika counter -->
<script type="text/javascript" >
   (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
   m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
   (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");

   ym(51621260, "init", {
        id:51621260,
        clickmap:true,
        trackLinks:true,
        accurateTrackBounce:true,
        webvisor:true
   });
</script>
<noscript><div><img src="https://mc.yandex.ru/watch/51621260" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
<!-- /Yandex.Metrika counter -->

<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-5727382-29"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'UA-5727382-29');
</script>
</body>
</html>

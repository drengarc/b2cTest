$(document).ready(function(e) {
	var $menutop =$('#block_top_menu');
	$(document).click(function(e){
		if($menutop.children('ul').css('display') == 'none' && $(e.target).is('.vt-menu-stick')){
			$menutop.children('ul').stop().show().animate({'left':0},500);
			$menutop.append('<div class="mobile-open"/>');
			$menutop.closest('body').addClass('body-mobile-open');			
		}else{
			if(!$(e.target).is('ul, li', $menutop)){
				$menutop.children('ul').stop().animate({'left':'-100%'},500).hide();
				$menutop.children('.mobile-open').remove();
				$menutop.closest('body').removeClass('body-mobile-open');
			}
		}
	});
});
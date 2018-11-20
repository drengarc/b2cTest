/*
* 2007-2014 PrestaShop
*
* NOTICE OF LICENSE
*
* This source file is subject to the Academic Free License (AFL 3.0)
* that is bundled with this package in the file LICENSE.txt.
* It is also available through the world-wide-web at this URL:
* http://opensource.org/licenses/afl-3.0.php
* If you did not receive a copy of the license and are unable to
* obtain it through the world-wide-web, please send an email
* to license@prestashop.com so we can send you a copy immediately.
*
* DISCLAIMER
*
* Do not edit or add to this file if you wish to upgrade PrestaShop to newer
* versions in the future. If you wish to customize PrestaShop for your
* needs please refer to http://www.prestashop.com for more information.
*
*  @author PrestaShop SA <contact@prestashop.com>
*  @copyright  2007-2014 PrestaShop SA
*  @license    http://opensource.org/licenses/afl-3.0.php  Academic Free License (AFL 3.0)
*  International Registered Trademark & Property of PrestaShop SA
*/
//global variables
var responsiveflag = false;
$(document).ready(function(){
	highdpi_init();
	blockHover();
	if (typeof quickView !== 'undefined' && quickView)
		quick_view();
	responsiveResize();
	$(window).resize(responsiveResize);
	tmDropDown ('', '#header .current', 'ul.toogle_content', 'active');							// all of this should be defined or left empty brackets
	//tmDropDown ('cart', 'li#shopping_cart > a', '#cart_block', 'active');			// all of this should be defined or left empty brackets
	if (navigator.userAgent.match(/Android/i))
	{
		var viewport = document.querySelector("meta[name=viewport]");
		viewport.setAttribute('content', 'initial-scale=1.0,maximum-scale=1.0,user-scalable=0,width=device-width,height=device-height');
	}
	if (navigator.userAgent.match(/Android/i))
		window.scrollTo(0,1);
	if (typeof page_name != 'undefined' && !in_array(page_name, ['index', 'product']))
	{
		/*
		var view = $.totalStorage('display');
		if (view && view != 'grid')
			display(view);
		else
			$('.display').find('li#grid').addClass('selected');
		
		$(document).on('click', '#grid', function(e){
			e.preventDefault();
			display('grid');
		});
		$(document).on('click', '#list', function(e){
			e.preventDefault();
			display('list');
		});
		*/
		
 		$(document).on('change', '.selectProductSort', function(){
			if (typeof request != 'undefined' && request)
				var requestSortProducts = request;
 			var splitData = $(this).val().split(':');
			if (typeof requestSortProducts != 'undefined' && requestSortProducts)
				document.location.href = requestSortProducts + ((requestSortProducts.indexOf('?') < 0) ? '?' : '&') + 'orderby=' + splitData[0] + '&orderway=' + splitData[1];
    	});
		$(document).on('change', 'select[name=n]', function(){
			$(this.form).submit();
		});
		$(document).on('change', 'select[name=manufacturer_list], select[name=supplier_list]', function(){
			autoUrl($(this).attr('id'), '');
		});
		$(document).on('change', 'select[name=currency_payement]', function(){
			setCurrency($(this).val());
		});
	}
	
	jQuery.curCSS = jQuery.css;
	if (!!$.prototype.cluetip)
		$('a.cluetip').cluetip({
			local:true,
			cursor: 'pointer',
			dropShadow: false,
			dropShadowSteps: 0,
			showTitle: false,
			tracking: true,
			sticky: false,
			mouseOutClose: true,
			fx: {             
		    	open:       'fadeIn',
		    	openSpeed:  'fast'
			}
		}).css('opacity', 0.8);

		$(document).on('click', '.back', function(e){
			e.preventDefault();
			history.back();
		});
});
function highdpi_init()
{
	if($('.replace-2x').css('font-size') == "1px")
	{		
		var els = $("img.replace-2x").get();
		for(var i = 0; i < els.length; i++)
		{
			src = els[i].src;
			extension = src.substr( (src.lastIndexOf('.') +1) );
			src = src.replace("."+extension, "2x."+extension);
			
			var img = new Image();
			img.src = src;
			img.height != 0 ? els[i].src = src : els[i].src = els[i].src;
		}
	}
}
function blockHover(status)
{
	$(document).off('mouseenter').on('mouseenter', '.product_list.grid li.ajax_block_product .product-container',
		function(e){
			if ($('body').find('.container').width() == 1170){
				var pcHeight = $(this).parent().outerHeight();
				var pcPHeight = $(this).parent().find('.button-container').outerHeight() + $(this).parent().find('.comments_note').outerHeight() + $(this).parent().find('.functional-buttons').outerHeight();
				$(this).parent().addClass('hovered');
				$(this).parent().css('height', pcHeight + pcPHeight).css('margin-bottom', pcPHeight * (-1));
			}
		}
	);
	$(document).off('mouseleave').on('mouseleave', '.product_list.grid li.ajax_block_product .product-container', function(e){
			if ($('body').find('.container').width() == 1170)
				$(this).parent().removeClass('hovered').removeAttr('style');
		}
	);
}
/*
function display(view)
{
	if (view == 'list')
	{
		$('ul.product_list').removeClass('grid').addClass('list row');
		$('.product_list > li').removeClass('col-xs-12 col-sm-6 col-md-4').addClass('col-xs-12');
		$('.product_list > li').each(function(index, element) {
			html = '';
			html = '<div class="product-container"><div class="row">';
				html += '<div class="left-block col-xs-4 col-xs-5 col-md-4">' + $(element).find('.left-block').html() + '</div>';
				html += '<div class="center-block col-xs-4 col-xs-7 col-md-4">';
					html += '<div class="product-flags">'+ $(element).find('.product-flags').html() + '</div>';
					html += '<h5 itemprop="name">'+ $(element).find('h5').html() + '</h5>';
					var rating = $(element).find('.comments_note').html(); // check : rating
					if (rating != null) { 
						html += '<div itemprop="aggregateRating" itemscope itemtype="http://schema.org/AggregateRating" class="comments_note">'+ rating + '</div>';
					}
					html += '<p class="product-desc">'+ $(element).find('.product-desc').html() + '</p>';
					var colorList = $(element).find('.color-list-container').html();
					if (colorList != null) {
						html += '<div class="color-list-container">'+ colorList +'</div>';
					}
					var availability = $(element).find('.availability').html();	// check : catalog mode is enabled
					if (availability != null) {
						html += '<span class="availability">'+ availability +'</span>';
					}
				html += '</div>';	
				html += '<div class="right-block col-xs-4 col-xs-12 col-md-4"><div class="right-block-content row">';
					var price = $(element).find('.content_price').html();       // check : catalog mode is enabled
					if (price != null) { 
						html += '<div class="content_price col-xs-5 col-md-12">'+ price + '</div>';
					}
					html += '<div class="button-container col-xs-7 col-md-12">'+ $(element).find('.button-container').html() +'</div>';
					html += '<div class="functional-buttons clearfix col-sm-12">' + $(element).find('.functional-buttons').html() + '</div>';
				html += '</div>';
			html += '</div></div>';
		$(element).html(html);
		});		
		$('.display').find('li#list').addClass('selected');
		$('.display').find('li#grid').removeAttr('class');
		$.totalStorage('display', 'list');
		if (typeof ajaxCart != 'undefined')      // cart button reload
			ajaxCart.overrideButtonsInThePage();
		if (typeof quickView !== 'undefined' && quickView) 	// qick view button reload
			quick_view();
	}
	else 
	{
		$('ul.product_list').removeClass('list').addClass('grid row');
		$('.product_list > li').removeClass('col-xs-12').addClass('col-xs-12 col-sm-6 col-md-4');
		$('.product_list > li').each(function(index, element) {
		html = '';
		html += '<div class="product-container">';
			html += '<div class="left-block">' + $(element).find('.left-block').html() + '</div>';
			html += '<div class="right-block">';
				html += '<div class="product-flags">'+ $(element).find('.product-flags').html() + '</div>';
				html += '<h5 itemprop="name">'+ $(element).find('h5').html() + '</h5>';
				var rating = $(element).find('.comments_note').html(); // check : rating
					if (rating != null) { 
						html += '<div itemprop="aggregateRating" itemscope itemtype="http://schema.org/AggregateRating" class="comments_note">'+ rating + '</div>';
					}
				html += '<p itemprop="description" class="product-desc">'+ $(element).find('.product-desc').html() + '</p>';
				var price = $(element).find('.content_price').html(); // check : catalog mode is enabled
					if (price != null) { 
						html += '<div class="content_price">'+ price + '</div>';
					}
				html += '<div itemprop="offers" itemscope itemtype="http://schema.org/Offer" class="button-container">'+ $(element).find('.button-container').html() +'</div>';
				var colorList = $(element).find('.color-list-container').html();
				if (colorList != null) {
					html += '<div class="color-list-container">'+ colorList +'</div>';
				}
				var availability = $(element).find('.availability').html(); // check : catalog mode is enabled
				if (availability != null) {
					html += '<span class="availability">'+ availability +'</span>';
				}
			html += '</div>';
			html += '<div class="functional-buttons clearfix">' + $(element).find('.functional-buttons').html() + '</div>';
		html += '</div>';		
		$(element).html(html);
		});
		$('.display').find('li#grid').addClass('selected');
		$('.display').find('li#list').removeAttr('class');
		$.totalStorage('display', 'grid');			
		if (typeof ajaxCart != 'undefined') 	// cart button reload
			ajaxCart.overrideButtonsInThePage();
		if (typeof quickView !== 'undefined' && quickView) 	// qick view button reload
			quick_view();
	}	
}
*/
function quick_view()
{
	$(document).on('click', '.quick-view', function(e) 
	{
		e.preventDefault();
		var url = this.rel;
		if (url.indexOf('?') != -1)
			url += '&';
		else
			url += '?';
		if (!!$.prototype.fancybox)
			$.fancybox({
				'padding':  0,
				'width':    1087,
				'height':   610,
				'type':     'iframe',
				'href':     url + 'content_only=1'
			});
	});
}
/*********************************************************** TMMenuDropDown **********************************/
function tmDropDown (elementType, elementClick, elementSlide, activeClass){
	elementType = elementType;           // special if hidden element isn't next (like for cart block here)
	elementClick = elementClick;         // element to click
	elementSlide =  elementSlide;        // element to show/hide
	activeClass = activeClass;			 // active class for "element to click"
	//show/hide elements
	$(elementClick).on('click touchstart', function(){
		if (elementType != 'cart')
			var subUl = $(this).next(elementSlide);
		else
			var subUl = $(this).parents('#header').find(elementSlide);
		if(subUl.is(':hidden')) {
			subUl.slideDown(),
			$(this).addClass(activeClass)	
		}
		else {
			subUl.slideUp(),
			$(this).removeClass(activeClass)
		}
		$(elementClick).not(this).next(elementSlide).slideUp(),
		$(elementClick).not(this).removeClass(activeClass);
		return false
	}),
	//enable clicks on showed elements
	$(elementSlide).on('click touchstart', function(e){
		e.stopPropagation();
	});
	// hide showed elements on document click
	$(document).on('click touchstart', function(){
		if (elementType != 'cart')
			var elementHide = $(elementClick).next(elementSlide);
		else
			var elementHide = $(elementClick).parents('#header').find(elementSlide);
			$(elementHide).slideUp(),
			$(elementClick).removeClass('active')
	})
}
//   TOGGLE FOOTER
function accordionFooter(status){
		if(status == 'enable'){
			$('#footer .footer-block h4').on('click', function(){
				$(this).toggleClass('active').parent().find('.toggle-footer').stop().slideToggle('medium');
			})
			$('#footer').addClass('accordion').find('.toggle-footer').slideUp('fast');
		}else{
			$('.footer-block h4').removeClass('active').off().parent().find('.toggle-footer').removeAttr('style').slideDown('fast');
			$('#footer').removeClass('accordion');
		}
	}
//   TOGGLE COLUMNS
function accordion(status){
		leftColumnBlocks = $('#left_column');
		if(status == 'enable'){
			$('#right_column .block:not(#layered_block_left) .title_block, #left_column .block:not(#layered_block_left) .title_block, #left_column #newsletter_block_left h4').on('click', function(){
				$(this).toggleClass('active').parent().find('.block_content').stop().slideToggle('medium');
			})
			$('#right_column, #left_column').addClass('accordion').find('.block:not(#layered_block_left) .block_content').slideUp('fast');
		}else{
			$('#right_column .block:not(#layered_block_left) .title_block, #left_column .block:not(#layered_block_left) .title_block, #left_column #newsletter_block_left h4').removeClass('active').off().parent().find('.block_content').removeAttr('style').slideDown('fast');
			$('#left_column, #right_column').removeClass('accordion');
		}
	}
function responsiveResize(){
	   if ($(document).width() <= 767 && responsiveflag == false){
	   		//accordion('enable');
		    accordionFooter('enable');
			responsiveflag = true;	
		}
		else if ($(document).width() >= 768){
			//accordion('disable');
			accordionFooter('disable');
	        responsiveflag = false;
		}
}
//CREATE THE PRODUCT GRID & LIST
(function($) {
	$(function() {
		function createCookie(name,value,days) {
			if (days) {
				var date = new Date();
				date.setTime(date.getTime()+(days*24*60*60*1000));
				var expires = "; expires="+date.toGMTString();
			}
			else var expires = "";
			document.cookie = name+"="+value+expires+"; path=/";
		}
		function readCookie(name) {
			var nameEQ = name + "=";
			var ca = document.cookie.split(';');
			for(var i=0;i < ca.length;i++) {
				var c = ca[i];
				while (c.charAt(0)==' ') c = c.substring(1,c.length);
				if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
			}
			return null;
		}
		function eraseCookie(name) {
			createCookie(name,"",-1);
		}
		var $productList = $('.product_list', '#center_column');
		$productList.addClass($('body').data('product-view'));
		if($('body').data('product-view') == 'list'){
			$('#product_view_list').addClass('current');
			$productList.children().addClass('col-md-12').removeClass('col-md-'+(12/$('body').data('view-grid')));
		}else{
			$('#product_view_grid').addClass('current');
			$productList.children().addClass('col-md-'+(12/$('body').data('view-grid'))).removeClass('col-md-12');
		}
		$('.product_view').each(function(i) {
			var cookie = readCookie('tabCookie'+i);
			if (cookie){ $(this).find('a').eq(cookie).addClass('current').siblings().removeClass('current')
				.parents('#center_column').find('.product_list').addClass('list').removeClass('grid').eq(cookie).addClass('grid').removeClass('list');
				if($productList.hasClass('list'))
					$productList.children().removeClass('col-md-'+(12/$('body').data('view-grid'))).addClass('col-md-12');
				else
					$productList.children().removeClass('col-md-12').addClass('col-md-'+(12/$('body').data('view-grid')));
			}
		});
		$('.product_view').delegate('a:not(.current)', 'click', function(i) {
			$(this).addClass('current').siblings().removeClass('current')
				.parents('#center_column').find('.product_list').removeClass('grid').addClass('list').eq($(this).index()).addClass('grid').removeClass('list');
				if($productList.hasClass('list'))
					$productList.children().removeClass('col-md-'+(12/$('body').data('view-grid'))).addClass('col-md-12');
				else
					$productList.children().removeClass('col-md-12').addClass('col-md-'+(12/$('body').data('view-grid')));
			var cookie = readCookie('tabCookie'+i);
			if (cookie){
				$(this).find('.product_list').eq(cookie).removeClass('grid').addClass('list').siblings().removeClass('list');
				if($productList.hasClass('list'))
					$productList.children().removeClass('col-md-'+(12/$('body').data('view-grid'))).addClass('col-md-12');
				else
					$productList.children().removeClass('col-md-12').addClass('col-md-'+(12/$('body').data('view-grid')));
			}
			var ulIndex = $('.product_view').index($(this).parents('.product_view'));
			eraseCookie('tabCookie'+ulIndex);
			createCookie('tabCookie'+ulIndex, $(this).index(), 365);
		});
	});	
})(jQuery);
// CREATE THE EQUAL HEIGHT
function equalHeight(group) {
	var tallest = 0;
	group.each(function() {
		var thisHeight = $(this).height();
		if(thisHeight > tallest) {
			tallest = thisHeight;
		}
	});
	//group.height(tallest);
	group.css("min-height", tallest);
}
$(document).ready(function(){
	equalHeight($(".top-column"));
	$("#back-top").hide();
	$(function () {
		$(window).scroll(function () {
			if ($(this).scrollTop() > 100)
				$('#back-top').fadeIn();
			else
				$('#back-top').fadeOut();
		});
		$('#back-top a').click(function () {
			$('body,html').animate({scrollTop: 0}, 800);
			return false;
		});
	});
	$('.block').addClass('panel panel-default').children('h4, .title_block').addClass('panel-heading').end().children('.block_content').addClass('panel-body');
	$('#manufacturer_list, #supplier_list').addClass('form-control');
	$('#compare_shipping').children('.SE_SubmitRefreshCard').addClass('form-group').find('.exclusive_large').addClass('btn btn-default');
	$('#compare_shipping').children('#availableCarriers').addClass('table-responsive').children().addClass('table');
	$('.vt_menu, .sf-menu').find('.sfHoverForce').addClass('active').parents('li').addClass('active');
	$('.block > .title_block').each(function(index, element) {
        if(!$(this).children('span, a').length) $(this).wrapInner('<span />');
    });
	$('[data-toggle="tooltip"], .tooltip').tooltip();
});
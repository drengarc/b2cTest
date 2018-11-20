//     Underscore.js 1.5.2
//     http://underscorejs.org
//     (c) 2009-2013 Jeremy Ashkenas, DocumentCloud and Investigative Reporters & Editors
//     Underscore may be freely distributed under the MIT license.
(function(){var n=this,t=n._,r={},e=Array.prototype,u=Object.prototype,i=Function.prototype,a=e.push,o=e.slice,c=e.concat,l=u.toString,f=u.hasOwnProperty,s=e.forEach,p=e.map,h=e.reduce,v=e.reduceRight,g=e.filter,d=e.every,m=e.some,y=e.indexOf,b=e.lastIndexOf,x=Array.isArray,w=Object.keys,_=i.bind,j=function(n){return n instanceof j?n:this instanceof j?(this._wrapped=n,void 0):new j(n)};"undefined"!=typeof exports?("undefined"!=typeof module&&module.exports&&(exports=module.exports=j),exports._=j):n._=j,j.VERSION="1.5.2";var A=j.each=j.forEach=function(n,t,e){if(null!=n)if(s&&n.forEach===s)n.forEach(t,e);else if(n.length===+n.length){for(var u=0,i=n.length;i>u;u++)if(t.call(e,n[u],u,n)===r)return}else for(var a=j.keys(n),u=0,i=a.length;i>u;u++)if(t.call(e,n[a[u]],a[u],n)===r)return};j.map=j.collect=function(n,t,r){var e=[];return null==n?e:p&&n.map===p?n.map(t,r):(A(n,function(n,u,i){e.push(t.call(r,n,u,i))}),e)};var E="Reduce of empty array with no initial value";j.reduce=j.foldl=j.inject=function(n,t,r,e){var u=arguments.length>2;if(null==n&&(n=[]),h&&n.reduce===h)return e&&(t=j.bind(t,e)),u?n.reduce(t,r):n.reduce(t);if(A(n,function(n,i,a){u?r=t.call(e,r,n,i,a):(r=n,u=!0)}),!u)throw new TypeError(E);return r},j.reduceRight=j.foldr=function(n,t,r,e){var u=arguments.length>2;if(null==n&&(n=[]),v&&n.reduceRight===v)return e&&(t=j.bind(t,e)),u?n.reduceRight(t,r):n.reduceRight(t);var i=n.length;if(i!==+i){var a=j.keys(n);i=a.length}if(A(n,function(o,c,l){c=a?a[--i]:--i,u?r=t.call(e,r,n[c],c,l):(r=n[c],u=!0)}),!u)throw new TypeError(E);return r},j.find=j.detect=function(n,t,r){var e;return O(n,function(n,u,i){return t.call(r,n,u,i)?(e=n,!0):void 0}),e},j.filter=j.select=function(n,t,r){var e=[];return null==n?e:g&&n.filter===g?n.filter(t,r):(A(n,function(n,u,i){t.call(r,n,u,i)&&e.push(n)}),e)},j.reject=function(n,t,r){return j.filter(n,function(n,e,u){return!t.call(r,n,e,u)},r)},j.every=j.all=function(n,t,e){t||(t=j.identity);var u=!0;return null==n?u:d&&n.every===d?n.every(t,e):(A(n,function(n,i,a){return(u=u&&t.call(e,n,i,a))?void 0:r}),!!u)};var O=j.some=j.any=function(n,t,e){t||(t=j.identity);var u=!1;return null==n?u:m&&n.some===m?n.some(t,e):(A(n,function(n,i,a){return u||(u=t.call(e,n,i,a))?r:void 0}),!!u)};j.contains=j.include=function(n,t){return null==n?!1:y&&n.indexOf===y?n.indexOf(t)!=-1:O(n,function(n){return n===t})},j.invoke=function(n,t){var r=o.call(arguments,2),e=j.isFunction(t);return j.map(n,function(n){return(e?t:n[t]).apply(n,r)})},j.pluck=function(n,t){return j.map(n,function(n){return n[t]})},j.where=function(n,t,r){return j.isEmpty(t)?r?void 0:[]:j[r?"find":"filter"](n,function(n){for(var r in t)if(t[r]!==n[r])return!1;return!0})},j.findWhere=function(n,t){return j.where(n,t,!0)},j.max=function(n,t,r){if(!t&&j.isArray(n)&&n[0]===+n[0]&&n.length<65535)return Math.max.apply(Math,n);if(!t&&j.isEmpty(n))return-1/0;var e={computed:-1/0,value:-1/0};return A(n,function(n,u,i){var a=t?t.call(r,n,u,i):n;a>e.computed&&(e={value:n,computed:a})}),e.value},j.min=function(n,t,r){if(!t&&j.isArray(n)&&n[0]===+n[0]&&n.length<65535)return Math.min.apply(Math,n);if(!t&&j.isEmpty(n))return 1/0;var e={computed:1/0,value:1/0};return A(n,function(n,u,i){var a=t?t.call(r,n,u,i):n;a<e.computed&&(e={value:n,computed:a})}),e.value},j.shuffle=function(n){var t,r=0,e=[];return A(n,function(n){t=j.random(r++),e[r-1]=e[t],e[t]=n}),e},j.sample=function(n,t,r){return arguments.length<2||r?n[j.random(n.length-1)]:j.shuffle(n).slice(0,Math.max(0,t))};var k=function(n){return j.isFunction(n)?n:function(t){return t[n]}};j.sortBy=function(n,t,r){var e=k(t);return j.pluck(j.map(n,function(n,t,u){return{value:n,index:t,criteria:e.call(r,n,t,u)}}).sort(function(n,t){var r=n.criteria,e=t.criteria;if(r!==e){if(r>e||r===void 0)return 1;if(e>r||e===void 0)return-1}return n.index-t.index}),"value")};var F=function(n){return function(t,r,e){var u={},i=null==r?j.identity:k(r);return A(t,function(r,a){var o=i.call(e,r,a,t);n(u,o,r)}),u}};j.groupBy=F(function(n,t,r){(j.has(n,t)?n[t]:n[t]=[]).push(r)}),j.indexBy=F(function(n,t,r){n[t]=r}),j.countBy=F(function(n,t){j.has(n,t)?n[t]++:n[t]=1}),j.sortedIndex=function(n,t,r,e){r=null==r?j.identity:k(r);for(var u=r.call(e,t),i=0,a=n.length;a>i;){var o=i+a>>>1;r.call(e,n[o])<u?i=o+1:a=o}return i},j.toArray=function(n){return n?j.isArray(n)?o.call(n):n.length===+n.length?j.map(n,j.identity):j.values(n):[]},j.size=function(n){return null==n?0:n.length===+n.length?n.length:j.keys(n).length},j.first=j.head=j.take=function(n,t,r){return null==n?void 0:null==t||r?n[0]:o.call(n,0,t)},j.initial=function(n,t,r){return o.call(n,0,n.length-(null==t||r?1:t))},j.last=function(n,t,r){return null==n?void 0:null==t||r?n[n.length-1]:o.call(n,Math.max(n.length-t,0))},j.rest=j.tail=j.drop=function(n,t,r){return o.call(n,null==t||r?1:t)},j.compact=function(n){return j.filter(n,j.identity)};var M=function(n,t,r){return t&&j.every(n,j.isArray)?c.apply(r,n):(A(n,function(n){j.isArray(n)||j.isArguments(n)?t?a.apply(r,n):M(n,t,r):r.push(n)}),r)};j.flatten=function(n,t){return M(n,t,[])},j.without=function(n){return j.difference(n,o.call(arguments,1))},j.uniq=j.unique=function(n,t,r,e){j.isFunction(t)&&(e=r,r=t,t=!1);var u=r?j.map(n,r,e):n,i=[],a=[];return A(u,function(r,e){(t?e&&a[a.length-1]===r:j.contains(a,r))||(a.push(r),i.push(n[e]))}),i},j.union=function(){return j.uniq(j.flatten(arguments,!0))},j.intersection=function(n){var t=o.call(arguments,1);return j.filter(j.uniq(n),function(n){return j.every(t,function(t){return j.indexOf(t,n)>=0})})},j.difference=function(n){var t=c.apply(e,o.call(arguments,1));return j.filter(n,function(n){return!j.contains(t,n)})},j.zip=function(){for(var n=j.max(j.pluck(arguments,"length").concat(0)),t=new Array(n),r=0;n>r;r++)t[r]=j.pluck(arguments,""+r);return t},j.object=function(n,t){if(null==n)return{};for(var r={},e=0,u=n.length;u>e;e++)t?r[n[e]]=t[e]:r[n[e][0]]=n[e][1];return r},j.indexOf=function(n,t,r){if(null==n)return-1;var e=0,u=n.length;if(r){if("number"!=typeof r)return e=j.sortedIndex(n,t),n[e]===t?e:-1;e=0>r?Math.max(0,u+r):r}if(y&&n.indexOf===y)return n.indexOf(t,r);for(;u>e;e++)if(n[e]===t)return e;return-1},j.lastIndexOf=function(n,t,r){if(null==n)return-1;var e=null!=r;if(b&&n.lastIndexOf===b)return e?n.lastIndexOf(t,r):n.lastIndexOf(t);for(var u=e?r:n.length;u--;)if(n[u]===t)return u;return-1},j.range=function(n,t,r){arguments.length<=1&&(t=n||0,n=0),r=arguments[2]||1;for(var e=Math.max(Math.ceil((t-n)/r),0),u=0,i=new Array(e);e>u;)i[u++]=n,n+=r;return i};var R=function(){};j.bind=function(n,t){var r,e;if(_&&n.bind===_)return _.apply(n,o.call(arguments,1));if(!j.isFunction(n))throw new TypeError;return r=o.call(arguments,2),e=function(){if(!(this instanceof e))return n.apply(t,r.concat(o.call(arguments)));R.prototype=n.prototype;var u=new R;R.prototype=null;var i=n.apply(u,r.concat(o.call(arguments)));return Object(i)===i?i:u}},j.partial=function(n){var t=o.call(arguments,1);return function(){return n.apply(this,t.concat(o.call(arguments)))}},j.bindAll=function(n){var t=o.call(arguments,1);if(0===t.length)throw new Error("bindAll must be passed function names");return A(t,function(t){n[t]=j.bind(n[t],n)}),n},j.memoize=function(n,t){var r={};return t||(t=j.identity),function(){var e=t.apply(this,arguments);return j.has(r,e)?r[e]:r[e]=n.apply(this,arguments)}},j.delay=function(n,t){var r=o.call(arguments,2);return setTimeout(function(){return n.apply(null,r)},t)},j.defer=function(n){return j.delay.apply(j,[n,1].concat(o.call(arguments,1)))},j.throttle=function(n,t,r){var e,u,i,a=null,o=0;r||(r={});var c=function(){o=r.leading===!1?0:new Date,a=null,i=n.apply(e,u)};return function(){var l=new Date;o||r.leading!==!1||(o=l);var f=t-(l-o);return e=this,u=arguments,0>=f?(clearTimeout(a),a=null,o=l,i=n.apply(e,u)):a||r.trailing===!1||(a=setTimeout(c,f)),i}},j.debounce=function(n,t,r){var e,u,i,a,o;return function(){i=this,u=arguments,a=new Date;var c=function(){var l=new Date-a;t>l?e=setTimeout(c,t-l):(e=null,r||(o=n.apply(i,u)))},l=r&&!e;return e||(e=setTimeout(c,t)),l&&(o=n.apply(i,u)),o}},j.once=function(n){var t,r=!1;return function(){return r?t:(r=!0,t=n.apply(this,arguments),n=null,t)}},j.wrap=function(n,t){return function(){var r=[n];return a.apply(r,arguments),t.apply(this,r)}},j.compose=function(){var n=arguments;return function(){for(var t=arguments,r=n.length-1;r>=0;r--)t=[n[r].apply(this,t)];return t[0]}},j.after=function(n,t){return function(){return--n<1?t.apply(this,arguments):void 0}},j.keys=w||function(n){if(n!==Object(n))throw new TypeError("Invalid object");var t=[];for(var r in n)j.has(n,r)&&t.push(r);return t},j.values=function(n){for(var t=j.keys(n),r=t.length,e=new Array(r),u=0;r>u;u++)e[u]=n[t[u]];return e},j.pairs=function(n){for(var t=j.keys(n),r=t.length,e=new Array(r),u=0;r>u;u++)e[u]=[t[u],n[t[u]]];return e},j.invert=function(n){for(var t={},r=j.keys(n),e=0,u=r.length;u>e;e++)t[n[r[e]]]=r[e];return t},j.functions=j.methods=function(n){var t=[];for(var r in n)j.isFunction(n[r])&&t.push(r);return t.sort()},j.extend=function(n){return A(o.call(arguments,1),function(t){if(t)for(var r in t)n[r]=t[r]}),n},j.pick=function(n){var t={},r=c.apply(e,o.call(arguments,1));return A(r,function(r){r in n&&(t[r]=n[r])}),t},j.omit=function(n){var t={},r=c.apply(e,o.call(arguments,1));for(var u in n)j.contains(r,u)||(t[u]=n[u]);return t},j.defaults=function(n){return A(o.call(arguments,1),function(t){if(t)for(var r in t)n[r]===void 0&&(n[r]=t[r])}),n},j.clone=function(n){return j.isObject(n)?j.isArray(n)?n.slice():j.extend({},n):n},j.tap=function(n,t){return t(n),n};var S=function(n,t,r,e){if(n===t)return 0!==n||1/n==1/t;if(null==n||null==t)return n===t;n instanceof j&&(n=n._wrapped),t instanceof j&&(t=t._wrapped);var u=l.call(n);if(u!=l.call(t))return!1;switch(u){case"[object String]":return n==String(t);case"[object Number]":return n!=+n?t!=+t:0==n?1/n==1/t:n==+t;case"[object Date]":case"[object Boolean]":return+n==+t;case"[object RegExp]":return n.source==t.source&&n.global==t.global&&n.multiline==t.multiline&&n.ignoreCase==t.ignoreCase}if("object"!=typeof n||"object"!=typeof t)return!1;for(var i=r.length;i--;)if(r[i]==n)return e[i]==t;var a=n.constructor,o=t.constructor;if(a!==o&&!(j.isFunction(a)&&a instanceof a&&j.isFunction(o)&&o instanceof o))return!1;r.push(n),e.push(t);var c=0,f=!0;if("[object Array]"==u){if(c=n.length,f=c==t.length)for(;c--&&(f=S(n[c],t[c],r,e)););}else{for(var s in n)if(j.has(n,s)&&(c++,!(f=j.has(t,s)&&S(n[s],t[s],r,e))))break;if(f){for(s in t)if(j.has(t,s)&&!c--)break;f=!c}}return r.pop(),e.pop(),f};j.isEqual=function(n,t){return S(n,t,[],[])},j.isEmpty=function(n){if(null==n)return!0;if(j.isArray(n)||j.isString(n))return 0===n.length;for(var t in n)if(j.has(n,t))return!1;return!0},j.isElement=function(n){return!(!n||1!==n.nodeType)},j.isArray=x||function(n){return"[object Array]"==l.call(n)},j.isObject=function(n){return n===Object(n)},A(["Arguments","Function","String","Number","Date","RegExp"],function(n){j["is"+n]=function(t){return l.call(t)=="[object "+n+"]"}}),j.isArguments(arguments)||(j.isArguments=function(n){return!(!n||!j.has(n,"callee"))}),"function"!=typeof/./&&(j.isFunction=function(n){return"function"==typeof n}),j.isFinite=function(n){return isFinite(n)&&!isNaN(parseFloat(n))},j.isNaN=function(n){return j.isNumber(n)&&n!=+n},j.isBoolean=function(n){return n===!0||n===!1||"[object Boolean]"==l.call(n)},j.isNull=function(n){return null===n},j.isUndefined=function(n){return n===void 0},j.has=function(n,t){return f.call(n,t)},j.noConflict=function(){return n._=t,this},j.identity=function(n){return n},j.times=function(n,t,r){for(var e=Array(Math.max(0,n)),u=0;n>u;u++)e[u]=t.call(r,u);return e},j.random=function(n,t){return null==t&&(t=n,n=0),n+Math.floor(Math.random()*(t-n+1))};var I={escape:{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#x27;"}};I.unescape=j.invert(I.escape);var T={escape:new RegExp("["+j.keys(I.escape).join("")+"]","g"),unescape:new RegExp("("+j.keys(I.unescape).join("|")+")","g")};j.each(["escape","unescape"],function(n){j[n]=function(t){return null==t?"":(""+t).replace(T[n],function(t){return I[n][t]})}}),j.result=function(n,t){if(null==n)return void 0;var r=n[t];return j.isFunction(r)?r.call(n):r},j.mixin=function(n){A(j.functions(n),function(t){var r=j[t]=n[t];j.prototype[t]=function(){var n=[this._wrapped];return a.apply(n,arguments),z.call(this,r.apply(j,n))}})};var N=0;j.uniqueId=function(n){var t=++N+"";return n?n+t:t},j.templateSettings={evaluate:/<%([\s\S]+?)%>/g,interpolate:/<%=([\s\S]+?)%>/g,escape:/<%-([\s\S]+?)%>/g};var q=/(.)^/,B={"'":"'","\\":"\\","\r":"r","\n":"n","	":"t","\u2028":"u2028","\u2029":"u2029"},D=/\\|'|\r|\n|\t|\u2028|\u2029/g;j.template=function(n,t,r){var e;r=j.defaults({},r,j.templateSettings);var u=new RegExp([(r.escape||q).source,(r.interpolate||q).source,(r.evaluate||q).source].join("|")+"|$","g"),i=0,a="__p+='";n.replace(u,function(t,r,e,u,o){return a+=n.slice(i,o).replace(D,function(n){return"\\"+B[n]}),r&&(a+="'+\n((__t=("+r+"))==null?'':_.escape(__t))+\n'"),e&&(a+="'+\n((__t=("+e+"))==null?'':__t)+\n'"),u&&(a+="';\n"+u+"\n__p+='"),i=o+t.length,t}),a+="';\n",r.variable||(a="with(obj||{}){\n"+a+"}\n"),a="var __t,__p='',__j=Array.prototype.join,"+"print=function(){__p+=__j.call(arguments,'');};\n"+a+"return __p;\n";try{e=new Function(r.variable||"obj","_",a)}catch(o){throw o.source=a,o}if(t)return e(t,j);var c=function(n){return e.call(this,n,j)};return c.source="function("+(r.variable||"obj")+"){\n"+a+"}",c},j.chain=function(n){return j(n).chain()};var z=function(n){return this._chain?j(n).chain():n};j.mixin(j),A(["pop","push","reverse","shift","sort","splice","unshift"],function(n){var t=e[n];j.prototype[n]=function(){var r=this._wrapped;return t.apply(r,arguments),"shift"!=n&&"splice"!=n||0!==r.length||delete r[0],z.call(this,r)}}),A(["concat","join","slice"],function(n){var t=e[n];j.prototype[n]=function(){return z.call(this,t.apply(this._wrapped,arguments))}}),j.extend(j.prototype,{chain:function(){return this._chain=!0,this},value:function(){return this._wrapped}})}).call(this);
//# sourceMappingURL=underscore-min.map

(function(e){if(typeof module==="function"){module.exports=e(this.jQuery||require("jquery"))}else{this.NProgress=e(this.jQuery)}})(function(e){function r(e,t,n){if(e<t)return t;if(e>n)return n;return e}function i(e){return(-1+e)*100}function s(e,t,r){var s;if(n.positionUsing==="translate3d"){s={transform:"translate3d("+i(e)+"%,0,0)"}}else if(n.positionUsing==="translate"){s={transform:"translate("+i(e)+"%,0)"}}else{s={"margin-left":i(e)+"%"}}s.transition="all "+t+"ms "+r;return s}var t={};t.version="0.1.2";var n=t.settings={minimum:.08,easing:"ease",positionUsing:"",speed:200,trickle:true,trickleRate:.02,trickleSpeed:800,showSpinner:true,template:'<div class="bar" role="bar"><div class="peg"></div></div><div class="spinner" role="spinner"><div class="spinner-icon"></div></div>'};t.configure=function(t){e.extend(n,t);return this};t.status=null;t.set=function(e){var i=t.isStarted();e=r(e,n.minimum,1);t.status=e===1?null:e;var o=t.render(!i),u=o.find('[role="bar"]'),a=n.speed,f=n.easing;o[0].offsetWidth;o.queue(function(r){if(n.positionUsing==="")n.positionUsing=t.getPositioningCSS();u.css(s(e,a,f));if(e===1){o.css({transition:"none",opacity:1});o[0].offsetWidth;setTimeout(function(){o.css({transition:"all "+a+"ms linear",opacity:0});setTimeout(function(){t.remove();r()},a)},a)}else{setTimeout(r,a)}});return this};t.isStarted=function(){return typeof t.status==="number"};t.start=function(){if(!t.status)t.set(0);var e=function(){setTimeout(function(){if(!t.status)return;t.trickle();e()},n.trickleSpeed)};if(n.trickle)e();return this};t.done=function(e){if(!e&&!t.status)return this;return t.inc(.3+.5*Math.random()).set(1)};t.inc=function(e){var n=t.status;if(!n){return t.start()}else{if(typeof e!=="number"){e=(1-n)*r(Math.random()*n,.1,.95)}n=r(n+e,0,.994);return t.set(n)}};t.trickle=function(){return t.inc(Math.random()*n.trickleRate)};t.render=function(r){if(t.isRendered())return e("#nprogress");e("html").addClass("nprogress-busy");var s=e("<div id='nprogress'>").html(n.template);var o=r?"-100":i(t.status||0);s.find('[role="bar"]').css({transition:"all 0 linear",transform:"translate3d("+o+"%,0,0)"});if(!n.showSpinner)s.find('[role="spinner"]').remove();s.appendTo(document.body);return s};t.remove=function(){e("html").removeClass("nprogress-busy");e("#nprogress").remove()};t.isRendered=function(){return e("#nprogress").length>0};t.getPositioningCSS=function(){var e=document.body.style;var t="WebkitTransform"in e?"Webkit":"MozTransform"in e?"Moz":"msTransform"in e?"ms":"OTransform"in e?"O":"";if(t+"Perspective"in e){return"translate3d"}else if(t+"Transform"in e){return"translate"}else{return"margin"}};return t})
NProgress.configure({ ease: 'ease', speed: 1000 });
NProgress.configure({ trickleRate: 0.5, trickleSpeed: 1600 });

if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

var box = function(data) {
    if(!data.height){data.height = 'auto'}
        if(!data.width){data.width = 'auto'}

        var id = $('.frontbox').length;


        if(data.type=='iframe') {
            var html = '<iframe height="'+(data.height-175)+'" width="'+(data.width-20)+'" frameborder="0" name="uvw-iframe" src="'+data.source+'">';
        }else {
            var html = data.source;
        }

        if(data.modal) {
            $('body').append("<div class='mask white' id='bodyMask'></div>");
        }

        var div = document.createElement("div");
        div.className = 'frontbox '+(data.classes ? data.classes : '');
        div.id = 'frontbox_'+id;
        div.innerHTML = _.template('<div class="boxHeader"><h3 class="title"><%= title %></h3><a class="close external sprite" title="Kapat"></a></div><div class="frontbox_source" style="padding:<%= padding %>"> <%= html %></div>', {'title': data.title, 'html' : html, 'id': $('.frontbox').length, 'id': id, padding: data.padding });
        document.body.appendChild(div);

        var elem = $(div);
        elem.height(data.height).width(data.width).css('margin-left', -elem.width()/2).css('margin-top', -elem.height()/2).fadeIn('fast');
        elem.find('.frontbox_source').height(elem.height()-35);
        $('body').addClass('noscroll');
        if(data.draggable==true) elem.draggable({ handler: "h3.title" });
        if(typeof(data.callback)=="function") {
            data.callback(elem);
        }
        if(typeof(data.close)=="function") {
            elem.find('a.close').click(function(e) { data.close(e);});
        }
        $(document).one('keyup.box',function(e) {
          if (e.keyCode == 27) {closeBox('frontbox_'+id)}   // esc
        });
        elem.find('a.close').click(function(e) { closeBox('frontbox_'+id)});
        return 'frontbox_'+id;
}
var closeBox = function(id) {
        if(typeof(id)=="string")
            $('#'+id).remove();
        else
            id.remove();
        $('#bodyMask').remove();
        $('body').removeClass('noscroll');
        $(document).off('keyup.box');
}
jQuery(document).ready(function () {
    $(document).on('click', '.tabSwitch h5', function (e) {
        var cls = e.currentTarget.getAttribute('data-class');
        var parent = $(e.currentTarget).parents('.tabMenu');
        parent.find('ul.menugroup').hide()
        parent.find('ul.' + cls).show();
        $(e.currentTarget).siblings('h5').removeClass('selected');
        $(e.currentTarget).addClass('selected');
    });

    $('.tabContainer').each(function () {
        var _this = $(this);
        var li = _this.find('.tabs li.active');
        _this.find('.container').hide();
        if(li.length==0) {
            _this.find('.container:first').show();
            _this.find('.tabs li:first').addClass('active');
        }else {

            $('#' + li.children().attr('data-href')).show();
        }
        _this.find('.tabs li a').click(function () {
            var t = $(this).attr('data-href');
            _this.find('.tabs li').removeClass('active');
            $(this).parents('li').addClass('active');

            _this.find('.container').hide();
            $('#' + t).show();

        });
    });

    $('#H-Login').click(function() {
        $(document).on('click.loginmodal', function(e) {
            if($(e.target).closest('.loginModal').length>0) return;
            $('.loginModal').removeClass('open');
            $(document).off('click.loginmodal');
        });
       $(this).parent().toggleClass('open');
    });

    $('.product-arac').click(function () {
        var $this = $(this);
        if ($this.hasClass('filled')) return;

        var id = $this.closest('.product-item').attr('data-id');
        $.get("/api/product/" + id + "/vehicles", function (data) {
            box({source: "<div class='vehicle_list'>"+data+"</div>", modal: true, title:"Ürünün geçerli olduğu araçlar"});

        });
    });
    $('.product-esdeger').click(function () {
        var $this = $(this);
        if ($this.hasClass('filled')) return;

        var id = $this.closest('.product-item').attr('data-id');
        $.get("/api/product/" + id + "/similar", function (data) {
            box({source: "<ul class='catalog-small-view list-view'>" + data + "</ul>", modal: true, width:600, title:"Eşdeğer Ürünler"});
        });
    });
    $('.product-oem').click(function () {
        var $this = $(this);
        if ($this.hasClass('filled')) return;

        var id = $this.closest('.product-item').attr('data-id');
        $.get("/api/product/" + id + "/oem", function (data) {
            box({source: "<ul class='catalog-small-view'>" + data + "</ul>", modal: true, title:"Oem Kodları"});
        });
    });

    $('.product-bilgi').click(function () {
        var $this = $(this);
        if ($this.hasClass('filled')) return;

        var id = $this.closest('.product-item').attr('data-id');
        $.get("/api/product/" + id + "/information", function (data) {
            box({source: "<ul class='catalog-small-view'>" + data + "</ul>", modal: true, title:"Ürün Bilgileri"});
        });
    });
    $('#order_selectbox').change(function () {
        document.location = this.value;
    });

    $('.item-magnify').click(function(e) {
        e.preventDefault();

        $(this).siblings('.image').elevateZoom({
          zoomType : "inner",
          cursor: "crosshair"
        });

    });
});
var delay = 300;
var UA = navigator.userAgent;


(function( $ ) {
    $.widget( "custom.combobox", {
      _create: function() {
        this.wrapper = $( "<span>" )
          .addClass( "custom-combobox" )
          .insertAfter( this.element );

        this.element.hide();
        this._createAutocomplete();
        this._createShowAllButton();
      },

      _createAutocomplete: function() {
        var selected = this.element.children( ":selected" ),
          value = selected.val() ? selected.text() : "";

        this.input = $( "<input>" )
          .appendTo( this.wrapper )
          .val( value )
          .attr( "title", "" )
          .addClass( "custom-combobox-input ui-widget ui-widget-content ui-state-default ui-corner-left" )
          .autocomplete({
            delay: 0,
            minLength: 0,
            source: $.proxy( this, "_source" )
          })
          .tooltip({
            tooltipClass: "ui-state-highlight"
          });

        this._on( this.input, {
          autocompleteselect: function( event, ui ) {
            ui.item.option.selected = true;
            this._trigger( "select", event, {
              item: ui.item.option
            });
          },

          autocompletechange: "_removeIfInvalid"
        });
      },

      _createShowAllButton: function() {
        var input = this.input,
          wasOpen = false;

        $( "<a>" )
          .attr( "tabIndex", -1 )
          .attr( "title", "Show All Items" )
          .tooltip()
          .appendTo( this.wrapper )
          .button({
            icons: {
              primary: "ui-icon-triangle-1-s"
            },
            text: false
          })
          .removeClass( "ui-corner-all" )
          .addClass( "custom-combobox-toggle ui-corner-right" )
          .mousedown(function() {
            wasOpen = input.autocomplete( "widget" ).is( ":visible" );
          })
          .click(function() {
            input.focus();

            // Close if already visible
            if ( wasOpen ) {
              return;
            }

            // Pass empty string as value to search for, displaying all results
            input.autocomplete( "search", "" );
          });
      },

      _source: function( request, response ) {
        var matcher = new RegExp( $.ui.autocomplete.escapeRegex(request.term), "i" );
        response( this.element.children( "option" ).map(function() {
          var text = $( this ).text();
          if ( this.value && ( !request.term || matcher.test(text) ) )
            return {
              label: text,
              value: text,
              option: this
            };
        }) );
      },

      _removeIfInvalid: function( event, ui ) {

        // Selected an item, nothing to do
        if ( ui.item ) {
          return;
        }

        // Search for a match (case-insensitive)
        var value = this.input.val(),
          valueLowerCase = value.toLowerCase(),
          valid = false;
        this.element.children( "option" ).each(function() {
          if ( $( this ).text().toLowerCase() === valueLowerCase ) {
            this.selected = valid = true;
            return false;
          }
        });

        // Found a match, nothing to do
        if ( valid ) {
          return;
        }

        // Remove invalid value
        this.input
          .val( "" )
          .attr( "title", value + " didn't match any item" )
          .tooltip( "open" );
        this.element.val( "" );
        this._delay(function() {
          this.input.tooltip( "close" ).attr( "title", "" );
        }, 2500 );
        this.input.data( "ui-autocomplete" ).term = "";
      },

      _destroy: function() {
        this.wrapper.remove();
        this.element.show();
      }
    });
  })( jQuery );

window.onbeforeunload = function (e) {
    NProgress.start();
}

$(function() {
    $( ".number").each(function() {
        var attribute = parseInt(this.getAttribute('data-step'));
        var maxAttr = parseInt(this.getAttribute('data-max'));
        var $2 = $(this);
            var back = function(e) {
                $2.val(attribute);
                e.preventDefault();
                alert("Ürün paket olarak satılmaktadır. "+attribute+" ve katlarını girmeniz gerekiyor.");
                return false;
            }
            var backMax = function(e) {
                $2.val(maxAttr);
                e.preventDefault();
                alert("Girdiğiniz değer ürünün stoktaki miktarından fazladır." + maxAttr + " Adet Sipariş Verebilirsiniz");
                return false;
            }

            $2.change(function(e) {
                if(attribute && ($2.val() % attribute != 0))
                    return back(e);

                if(maxAttr && ($2.val() > maxAttr))
                    return backMax(e);
            });

            $2.keypress(function(e) {
                var code = e.keyCode || e.which;
                if (code == 13) {
                    if($2.val() % attribute != 0)
                        return back(e);
                    if($2.val() > maxAttr)
                        return backMax(e);

                }
            });

        $2.spinner({min: 0, width:30, max: maxAttr, step: attribute||1});
    });

    $('.filter-input').each(function () {
            var result;
            var performSearch = function (e) {
                var $this = $(e.currentTarget), query = $this.val().toLowerCase();
                var $target = $('#' + $this.attr('data-target'));
                if (result) {
                    result.remove();
                    result = null;
                }
                if (query == '')
                    $this.closest('.filter-container').find('.filter-close').hide();
                else
                    $this.closest('.filter-container').find('.filter-close').show();

                var count = 0;
                $target.children('li').each(function (idx, item) {
                    if (item.getAttribute('data').indexOf(query) > -1) {
                        item.style.display = 'block';
                        count += 1;
                    } else {
                        item.style.display = 'none';
                    }
                });

                if (count == 0) {
                    result = $(document.createElement('p')).html($this.attr('data-notfound')).css('margin', "10px");
                    $this.after(result);
                }

            }
            $(this).on('keyup', performSearch).on('search', function (e) {
                if ($(this).val() == '')
                    performSearch(e);
            });

            $('.filter-close').click(function () {
                $(this).hide().closest('.filter-container').find('.filter-input').val('').trigger('keyup');
            });
        });

    $('.category_selectbox').change(function () {
            document.location = this.value;
        });
        $('.number').keydown(function (e) {
            var a = e.keyCode;
            var k = this.value + String.fromCharCode(e.keyCode);
            if (k != parseInt(k) && !(a == null || a == 0 || a == 8 || a == 9 || a == 13 || a == 27)) e.preventDefault();
        });
});

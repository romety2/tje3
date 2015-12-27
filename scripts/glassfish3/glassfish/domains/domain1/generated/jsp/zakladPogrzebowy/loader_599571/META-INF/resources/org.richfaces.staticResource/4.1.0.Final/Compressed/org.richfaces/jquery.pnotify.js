(function(D){var I,A;
var E;
var B;
D.extend({pnotify_remove_all:function(){var K=E.data("pnotify");
if(K&&K.length){D.each(K,function(){if(this.pnotify_remove){this.pnotify_remove()
}})
}},pnotify_position_all:function(){if(A){clearTimeout(A)
}A=null;
var K=E.data("pnotify");
if(!K||!K.length){return 
}D.each(K,function(){var O=this.opts.pnotify_stack;
if(!O){return 
}if(!O.nextpos1){O.nextpos1=O.firstpos1
}if(!O.nextpos2){O.nextpos2=O.firstpos2
}if(!O.addpos2){O.addpos2=0
}if(this.css("display")!="none"){var Q,P;
var L={};
var N;
switch(O.dir1){case"down":N="top";
break;
case"up":N="bottom";
break;
case"left":N="right";
break;
case"right":N="left";
break
}Q=parseInt(this.css(N));
if(isNaN(Q)){Q=0
}if(typeof O.firstpos1=="undefined"){O.firstpos1=Q;
O.nextpos1=O.firstpos1
}var M;
switch(O.dir2){case"down":M="top";
break;
case"up":M="bottom";
break;
case"left":M="right";
break;
case"right":M="left";
break
}P=parseInt(this.css(M));
if(isNaN(P)){P=0
}if(typeof O.firstpos2=="undefined"){O.firstpos2=P;
O.nextpos2=O.firstpos2
}if((O.dir1=="down"&&O.nextpos1+this.height()>B.height())||(O.dir1=="up"&&O.nextpos1+this.height()>B.height())||(O.dir1=="left"&&O.nextpos1+this.width()>B.width())||(O.dir1=="right"&&O.nextpos1+this.width()>B.width())){O.nextpos1=O.firstpos1;
O.nextpos2+=O.addpos2+10;
O.addpos2=0
}if(O.animation&&O.nextpos2<P){switch(O.dir2){case"down":L.top=O.nextpos2+"px";
break;
case"up":L.bottom=O.nextpos2+"px";
break;
case"left":L.right=O.nextpos2+"px";
break;
case"right":L.left=O.nextpos2+"px";
break
}}else{this.css(M,O.nextpos2+"px")
}switch(O.dir2){case"down":case"up":if(this.outerHeight(true)>O.addpos2){O.addpos2=this.height()
}break;
case"left":case"right":if(this.outerWidth(true)>O.addpos2){O.addpos2=this.width()
}break
}if(O.nextpos1){if(O.animation&&(Q>O.nextpos1||L.top||L.bottom||L.right||L.left)){switch(O.dir1){case"down":L.top=O.nextpos1+"px";
break;
case"up":L.bottom=O.nextpos1+"px";
break;
case"left":L.right=O.nextpos1+"px";
break;
case"right":L.left=O.nextpos1+"px";
break
}}else{this.css(N,O.nextpos1+"px")
}}if(L.top||L.bottom||L.right||L.left){this.animate(L,{duration:500,queue:false})
}switch(O.dir1){case"down":case"up":O.nextpos1+=this.height()+10;
break;
case"left":case"right":O.nextpos1+=this.width()+10;
break
}}});
D.each(K,function(){var L=this.opts.pnotify_stack;
if(!L){return 
}L.nextpos1=L.firstpos1;
L.nextpos2=L.firstpos2;
L.addpos2=0;
L.animation=true
})
},pnotify:function(R){if(!E){E=D("body")
}if(!B){B=D(window)
}var S;
var K;
if(typeof R!="object"){K=D.extend({},D.pnotify.defaults);
K.pnotify_text=R
}else{K=D.extend({},D.pnotify.defaults,R);
if(K.pnotify_animation instanceof Object){K.pnotify_animation=D.extend({effect_in:D.pnotify.defaults.pnotify_animation,effect_out:D.pnotify.defaults.pnotify_animation},K.pnotify_animation)
}}if(K.pnotify_before_init){if(K.pnotify_before_init(K)===false){return null
}}var L;
var M=function(X,U){O.css("display","none");
var T=document.elementFromPoint(X.clientX,X.clientY);
O.css("display","block");
var W=D(T);
var V=W.css("cursor");
O.css("cursor",V!="auto"?V:"default");
if(!L||L.get(0)!=T){if(L){F.call(L.get(0),"mouseleave",X.originalEvent);
F.call(L.get(0),"mouseout",X.originalEvent)
}F.call(T,"mouseenter",X.originalEvent);
F.call(T,"mouseover",X.originalEvent)
}F.call(T,U,X.originalEvent);
L=W
};
var O=D("<div />",{"class":"rf-ntf "+K.pnotify_addclass,css:{display:"none"},mouseenter:function(T){if(K.pnotify_nonblock){T.stopPropagation()
}if(K.pnotify_mouse_reset&&S=="out"){O.stop(true);
S="in";
O.css("height","auto").animate({width:K.pnotify_width,opacity:K.pnotify_nonblock?K.pnotify_nonblock_opacity:K.pnotify_opacity},"fast")
}if(K.pnotify_nonblock){O.animate({opacity:K.pnotify_nonblock_opacity},"fast")
}if(K.pnotify_hide&&K.pnotify_mouse_reset){O.pnotify_cancel_remove()
}if(K.pnotify_closer&&!K.pnotify_nonblock){O.closer.css("visibility","visible")
}},mouseleave:function(T){if(K.pnotify_nonblock){T.stopPropagation()
}L=null;
O.css("cursor","auto");
if(K.pnotify_nonblock&&S!="out"){O.animate({opacity:K.pnotify_opacity},"fast")
}if(K.pnotify_hide&&K.pnotify_mouse_reset){O.pnotify_queue_remove()
}O.closer.css("visibility","hidden");
D.pnotify_position_all()
},mouseover:function(T){if(K.pnotify_nonblock){T.stopPropagation()
}},mouseout:function(T){if(K.pnotify_nonblock){T.stopPropagation()
}},mousemove:function(T){if(K.pnotify_nonblock){T.stopPropagation();
M(T,"onmousemove")
}},mousedown:function(T){if(K.pnotify_nonblock){T.stopPropagation();
T.preventDefault();
M(T,"onmousedown")
}},mouseup:function(T){if(K.pnotify_nonblock){T.stopPropagation();
T.preventDefault();
M(T,"onmouseup")
}},click:function(T){if(K.pnotify_nonblock){T.stopPropagation();
M(T,"onclick")
}},dblclick:function(T){if(K.pnotify_nonblock){T.stopPropagation();
M(T,"ondblclick")
}}});
O.opts=K;
if(K.pnotify_shadow&&!D.browser.msie){O.shadow_container=D("<div />",{"class":"rf-ntf-shdw"}).prependTo(O)
}O.container=D("<div />",{"class":"rf-ntf-cnt"}).appendTo(O);
O.pnotify_version="1.0.1";
O.pnotify=function(T){var U=K;
if(typeof T=="string"){K.pnotify_text=T
}else{K=D.extend({},K,T)
}O.opts=K;
if(K.pnotify_shadow!=U.pnotify_shadow){if(K.pnotify_shadow&&!D.browser.msie){O.shadow_container=D("<div />",{"class":"rf-ntf-shdw"}).prependTo(O)
}else{O.children(".rf-ntf-shdw").remove()
}}if(K.pnotify_addclass===false){O.removeClass(U.pnotify_addclass)
}else{if(K.pnotify_addclass!==U.pnotify_addclass){O.removeClass(U.pnotify_addclass).addClass(K.pnotify_addclass)
}}if(K.pnotify_title===false){O.title_container.hide("fast")
}else{if(K.pnotify_title!==U.pnotify_title){O.title_container.html(K.pnotify_title).show(200)
}}if(K.pnotify_text===false){O.text_container.hide("fast")
}else{if(K.pnotify_text!==U.pnotify_text){if(K.pnotify_insert_brs){K.pnotify_text=K.pnotify_text.replace(/\n/g,"<br />")
}O.text_container.html(K.pnotify_text).show(200)
}}O.pnotify_history=K.pnotify_history;
if(K.pnotify_type!=U.pnotify_type){O.container.toggleClass("rf-ntf-cnt rf-ntf-cnt-hov")
}if((K.pnotify_notice_icon!=U.pnotify_notice_icon&&K.pnotify_type=="notice")||(K.pnotify_error_icon!=U.pnotify_error_icon&&K.pnotify_type=="error")||(K.pnotify_type!=U.pnotify_type)){O.container.find("div.rf-ntf-ico").remove();
D("<div />",{"class":"rf-ntf-ico"}).append(D("<span />",{"class":K.pnotify_type=="error"?K.pnotify_error_icon:K.pnotify_notice_icon})).prependTo(O.container)
}if(K.pnotify_width!==U.pnotify_width){O.animate({width:K.pnotify_width})
}if(K.pnotify_min_height!==U.pnotify_min_height){O.container.animate({minHeight:K.pnotify_min_height})
}if(K.pnotify_opacity!==U.pnotify_opacity){O.fadeTo(K.pnotify_animate_speed,K.pnotify_opacity)
}if(!K.pnotify_hide){O.pnotify_cancel_remove()
}else{if(!U.pnotify_hide){O.pnotify_queue_remove()
}}O.pnotify_queue_position();
return O
};
O.pnotify_queue_position=function(){if(A){clearTimeout(A)
}A=setTimeout(D.pnotify_position_all,10)
};
O.pnotify_display=function(){if(!O.parent().length){O.appendTo(E)
}if(K.pnotify_before_open){if(K.pnotify_before_open(O)===false){return 
}}O.pnotify_queue_position();
if(K.pnotify_animation=="fade"||K.pnotify_animation.effect_in=="fade"){O.show().fadeTo(0,0).hide()
}else{if(K.pnotify_opacity!=1){O.show().fadeTo(0,K.pnotify_opacity).hide()
}}O.animate_in(function(){if(K.pnotify_after_open){K.pnotify_after_open(O)
}O.pnotify_queue_position();
if(K.pnotify_hide){O.pnotify_queue_remove()
}})
};
O.pnotify_remove=function(){if(O.timer){window.clearTimeout(O.timer);
O.timer=null
}if(K.pnotify_before_close){if(K.pnotify_before_close(O)===false){return 
}}O.animate_out(function(){if(K.pnotify_after_close){if(K.pnotify_after_close(O)===false){return 
}}O.pnotify_queue_position();
if(K.pnotify_remove){O.detach()
}})
};
O.animate_in=function(U){S="in";
var T;
if(typeof K.pnotify_animation.effect_in!="undefined"){T=K.pnotify_animation.effect_in
}else{T=K.pnotify_animation
}if(T=="none"){O.show();
U()
}else{if(T=="show"){O.show(K.pnotify_animate_speed,U)
}else{if(T=="fade"){O.show().fadeTo(K.pnotify_animate_speed,K.pnotify_opacity,U)
}else{if(T=="slide"){O.slideDown(K.pnotify_animate_speed,U)
}else{if(typeof T=="function"){T("in",U,O)
}else{if(O.effect){O.effect(T,{},K.pnotify_animate_speed,U)
}}}}}}};
O.animate_out=function(U){S="out";
var T;
if(typeof K.pnotify_animation.effect_out!="undefined"){T=K.pnotify_animation.effect_out
}else{T=K.pnotify_animation
}if(T=="none"){O.hide();
U()
}else{if(T=="show"){O.hide(K.pnotify_animate_speed,U)
}else{if(T=="fade"){O.fadeOut(K.pnotify_animate_speed,U)
}else{if(T=="slide"){O.slideUp(K.pnotify_animate_speed,U)
}else{if(typeof T=="function"){T("out",U,O)
}else{if(O.effect){O.effect(T,{},K.pnotify_animate_speed,U)
}}}}}}};
O.pnotify_cancel_remove=function(){if(O.timer){window.clearTimeout(O.timer)
}};
O.pnotify_queue_remove=function(){O.pnotify_cancel_remove();
O.timer=window.setTimeout(function(){O.pnotify_remove()
},(isNaN(K.pnotify_delay)?0:K.pnotify_delay))
};
O.closer=D("<div />",{"class":"rf-ntf-cls",css:{cursor:"pointer",visibility:"hidden"},click:function(){O.pnotify_remove();
O.closer.css("visibility","hidden")
}}).append(D("<span />",{"class":"rf-ntf-cls-ico"})).appendTo(O.container);
D("<div />",{"class":"rf-ntf-ico"}).append(D("<span />",{"class":K.pnotify_type=="error"?K.pnotify_error_icon:K.pnotify_notice_icon})).appendTo(O.container);
O.title_container=D("<div />",{"class":"rf-ntf-sum",html:K.pnotify_title}).appendTo(O.container);
if(K.pnotify_title===false){O.title_container.hide()
}if(K.pnotify_insert_brs&&typeof K.pnotify_text=="string"){K.pnotify_text=K.pnotify_text.replace(/\n/g,"<br />")
}O.text_container=D("<div />",{"class":"rf-ntf-det",html:K.pnotify_text}).appendTo(O.container);
if(K.pnotify_text===false){O.text_container.hide()
}D("<div />",{"class":"rf-ntf-clr"}).appendTo(O.container);
if(typeof K.pnotify_width=="string"){O.css("width",K.pnotify_width)
}if(typeof K.pnotify_min_height=="string"){O.container.css("min-height",K.pnotify_min_height)
}O.pnotify_history=K.pnotify_history;
var Q=E.data("pnotify");
if(Q==null||typeof Q!="object"){Q=[]
}if(K.pnotify_stack.push=="top"){Q=D.merge([O],Q)
}else{Q=D.merge(Q,[O])
}E.data("pnotify",Q);
if(K.pnotify_after_init){K.pnotify_after_init(O)
}if(K.pnotify_history){var P=E.data("pnotify_history");
if(typeof P=="undefined"){P=D("<div />",{"class":"rf-ntf-hstr",mouseleave:function(){P.animate({top:"-"+I+"px"},{duration:100,queue:false})
}}).append(D("<div />",{"class":"rf-ntf-hstr-hdr",text:"Redisplay"})).append(D("<button />",{"class":"rf-ntf-hstr-all",text:"All",click:function(){D.each(E.data("pnotify"),function(){if(this.pnotify_history&&this.pnotify_display){this.pnotify_display()
}});
return false
}})).append(D("<button />",{"class":"rf-ntf-hstr-last",text:"Last",click:function(){var T=1;
var U=E.data("pnotify");
while(!U[U.length-T]||!U[U.length-T].pnotify_history||U[U.length-T].is(":visible")){if(U.length-T===0){return false
}T++
}var V=U[U.length-T];
if(V.pnotify_display){V.pnotify_display()
}return false
}})).appendTo(E);
var N=D("<span />",{"class":"rf-ntf-hstr-hndl",mouseenter:function(){P.animate({top:"0"},{duration:100,queue:false})
}}).appendTo(P);
I=N.offset().top+2;
P.css({top:"-"+I+"px"});
E.data("pnotify_history",P)
}}K.pnotify_stack.animation=false;
O.pnotify_display();
return O
}});
var J=/^on/;
var C=/^(dbl)?click$|^mouse(move|down|up|over|out|enter|leave)$|^contextmenu$/;
var H=/^(focus|blur|select|change|reset)$|^key(press|down|up)$/;
var G=/^(scroll|resize|(un)?load|abort|error)$/;
var F=function(L,K){var M;
L=L.toLowerCase();
if(document.createEvent&&this.dispatchEvent){L=L.replace(J,"");
if(L.match(C)){D(this).offset();
M=document.createEvent("MouseEvents");
M.initMouseEvent(L,K.bubbles,K.cancelable,K.view,K.detail,K.screenX,K.screenY,K.clientX,K.clientY,K.ctrlKey,K.altKey,K.shiftKey,K.metaKey,K.button,K.relatedTarget)
}else{if(L.match(H)){M=document.createEvent("UIEvents");
M.initUIEvent(L,K.bubbles,K.cancelable,K.view,K.detail)
}else{if(L.match(G)){M=document.createEvent("HTMLEvents");
M.initEvent(L,K.bubbles,K.cancelable)
}}}if(!M){return 
}this.dispatchEvent(M)
}else{if(!L.match(J)){L="on"+L
}M=document.createEventObject(K);
this.fireEvent(L,M)
}};
D.pnotify.defaults={pnotify_title:false,pnotify_text:false,pnotify_addclass:"",pnotify_nonblock:false,pnotify_nonblock_opacity:0.2,pnotify_history:true,pnotify_width:"300px",pnotify_min_height:"16px",pnotify_type:"notice",pnotify_notice_icon:"",pnotify_error_icon:"",pnotify_animation:"fade",pnotify_animate_speed:"slow",pnotify_opacity:1,pnotify_shadow:false,pnotify_closer:true,pnotify_hide:true,pnotify_delay:8000,pnotify_mouse_reset:true,pnotify_remove:true,pnotify_insert_brs:true,pnotify_stack:{dir1:"down",dir2:"left",push:"bottom"}}
})(jQuery);
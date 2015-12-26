(function(F,I){I.ui=I.ui||{};
var E={styleClass:"",nonblocking:false,nonblockingOpacity:0.2,showHistory:false,animationSpeed:"slow",opacity:"1",showShadow:false,showCloseButton:true,appearAnimation:"fade",hideAnimation:"fade",sticky:false,stayTime:8000,delay:0};
var H="org.richfaces.notifyStack.default";
var J={summary:"pnotify_title",detail:"pnotify_text",styleClass:"pnotify_addclass",nonblocking:"pnotify_nonblock",nonblockingOpacity:"pnotify_nonblock_opacity",showHistory:"pnotify_history",animation:"pnotify_animation",appearAnimation:"effect_in",hideAnimation:"effect_out",animationSpeed:"pnotify_animate_speed",opacity:"pnotify_opacity",showShadow:"pnotify_shadow",showCloseButton:"pnotify_closer",sticky:"pnotify_hide",stayTime:"pnotify_delay"};
var B=["rf-ntf-inf","rf-ntf-wrn","rf-ntf-err","rf-ntf-ftl"];
var G=function(N,M,O){for(var K in M){var L=O[K]!=null?O[K]:K;
N[L]=M[K];
if(N[L] instanceof Object){N[L]=extend({},N[L],O)
}}return N
};
var D=function(){if(!document.getElementById(H)){var K=F('<span id="'+H+'" class="rf-ntf-stck" />');
F("body").append(K);
new RichFaces.ui.NotifyStack(H)
}return C(H)
};
var C=function(K){if(!K){return D()
}return I.$(K).getStack()
};
var A=function(N,M,L){var K=N.slice((L||M)+1||N.length);
N.length=M<0?N.length+M:M;
return N.push.apply(N,K)
};
I.ui.Notify=function(L){var L=F.extend({},E,L);
if(typeof L.severity=="number"){var K=B[L.severity];
L.styleClass=L.styleClass?K+" "+L.styleClass:K
}var M=G({},L,J);
var N=function(){var O=C(L.stackId);
M.pnotify_stack=O;
M.pnotify_addclass+=" rf-ntf-pos-"+O.position;
M.pnotify_after_close=function(Q){var R=F.inArray(Q,O.notifications);
if(R>=0){A(O.notifications,R)
}};
var P=F.pnotify(M);
O.addNotification(P)
};
if(L.sticky!==null){M.pnotify_hide=!L.sticky
}F(document).ready(function(){if(L.delay){setTimeout(function(){N()
},L.delay)
}else{N()
}})
}
})(jQuery,RichFaces);
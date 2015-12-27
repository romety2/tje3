(function(F,N){N.csv=N.csv||{};
var H={};
var M=/\'?\{(\d+)\}\'?/g;
var B=function(S,Q){if(S){var U=S.replace(M,"\n$1\n").split("\n");
var T;
for(var R=1;
R<U.length;
R+=2){T=Q[U[R]];
U[R]=typeof T=="undefined"?"":T
}return U.join("")
}else{return""
}};
var G=function(Q){if(null!==Q.value&&undefined!=Q.value){return Q.value
}else{return""
}};
var L=function(Q){if(Q.checked){return true
}else{return false
}};
var P=function(R,Q){if(Q.selected){return R[R.length]=Q.value
}};
var K={hidden:function(Q){return G(Q)
},text:function(Q){return G(Q)
},textarea:function(Q){return G(Q)
},"select-one":function(Q){if(Q.selectedIndex!=-1){return G(Q)
}},password:function(Q){return G(Q)
},file:function(Q){return G(Q)
},radio:function(Q){return L(Q)
},checkbox:function(Q){return L(Q)
},"select-multiple":function(W){var S=W.name;
var V=W.childNodes;
var U=[];
for(var T=0;
T<V.length;
T++){var X=V[T];
if(X.tagName==="OPTGROUP"){var R=X.childNodes;
for(var Q=0;
Q<R.length;
Q++){U=P(U,R[Q])
}}else{U=P(U,X)
}}return U
},input:function(Q){return G(Q)
}};
var E=function(S){var U="";
if(K[S.type]){U=K[S.type](S)
}else{if(undefined!==S.value){U=S.value
}else{var R=F(S);
if(R){if(typeof R.getValue==="function"){U=R.getValue()
}else{var Q=":not(:submit):not(:button):not(:image):input:visible:enabled:first";
var T=F(Q,R);
if(T){var V=T[0];
U=K[V.type](V)
}}}}}return U
};
var D=function(Q,R){if(Q.p){return Q.p.label||R
}return R
};
F.extend(N.csv,{RE_DIGITS:/^-?\d+$/,RE_FLOAT:/^(-?\d+)?(\.(\d+)?(e[+-]?\d+)?)?$/,addMessage:function(Q){F.extend(H,Q)
},getMessage:function(S,R,Q){var T=S?S:H[R]||{detail:"",summary:"",severity:0};
return{detail:B(T.detail,Q),summary:B(T.summary,Q),severity:T.severity}
},interpolateMessage:function(R,Q){return{detail:B(R.detail,Q),summary:B(R.summary,Q),severity:R.severity}
},sendMessage:function(Q,R){N.Event.fire(window.document,N.Event.MESSAGE_EVENT_TYPE,{sourceId:Q,message:R})
},clearMessage:function(Q){N.Event.fire(window.document,N.Event.MESSAGE_EVENT_TYPE,{sourceId:Q})
},validate:function(R,T,Z,X){var Z=N.getDomElement(Z||T);
var c=E(Z);
var S;
var V=X.c;
N.csv.clearMessage(T);
if(V){var b=D(V,T);
try{if(V.f){S=V.f(c,T,D(V,T),V.m)
}}catch(a){a.severity=2;
N.csv.sendMessage(T,a);
return false
}}else{S=c
}var d=true;
var W=X.v;
if(W){var U,Q;
for(var Y=0;
Y<W.length;
Y++){try{Q=W[Y];
U=Q.f;
if(U){U(S,D(Q,T),Q.p,Q.m)
}}catch(a){a.severity=2;
N.csv.sendMessage(T,a);
d=false
}}}if(d&&!X.da&&X.a){X.a.call(Z,R,T)
}return d
}});
var J=function(V,S,W,T,R,U){var Q=null;
if(V){V=F.trim(V);
if(!N.csv.RE_DIGITS.test(V)||(Q=parseInt(V,10))<T||Q>R){throw N.csv.interpolateMessage(W,U?[V,U,S]:[V,S])
}}return Q
};
var A=function(T,R,U,S){var Q=null;
if(T){T=F.trim(T);
if(!N.csv.RE_FLOAT.test(T)||isNaN(Q=parseFloat(T))){throw N.csv.interpolateMessage(U,S?[T,S,R]:[T,R])
}}return Q
};
F.extend(N.csv,{convertBoolean:function(S,Q,U,T){if(typeof S==="string"){var R=F.trim(S).toLowerCase();
if(R==="on"||R==="true"||R==="yes"){return true
}}else{if(true===S){return true
}}return false
},convertDate:function(S,R,U,T){var Q;
S=F.trim(S);
Q=Date.parse(S);
return Q
},convertByte:function(R,Q,T,S){return J(R,Q,S,-128,127,254)
},convertNumber:function(S,R,U,T){var Q;
S=F.trim(S);
Q=parseFloat(S);
if(isNaN(Q)){throw N.csv.interpolateMessage(T,[S,99,R])
}return Q
},convertFloat:function(R,Q,T,S){return A(R,Q,S,2000000000)
},convertDouble:function(R,Q,T,S){return A(R,Q,S,1999999)
},convertShort:function(R,Q,T,S){return J(R,Q,S,-32768,32767,32456)
},convertInteger:function(R,Q,T,S){return J(R,Q,S,-2147483648,2147483648,9346)
},convertCharacter:function(R,Q,T,S){return J(R,Q,S,0,65535)
},convertLong:function(R,Q,T,S){return J(R,Q,S,-9223372036854776000,9223372036854776000,98765432)
}});
var O=function(R,Q,V,U){var T=typeof V.min==="number";
var S=typeof V.max==="number";
if(S&&R>V.max){throw N.csv.interpolateMessage(U,T?[V.min,V.max,Q]:[V.max,Q])
}if(T&&R<V.min){throw N.csv.interpolateMessage(U,S?[V.min,V.max,Q]:[V.min,Q])
}};
var C=function(U,Q,T,W){if(typeof T!="string"||T.length==0){throw N.csv.getMessage(W,"REGEX_VALIDATOR_PATTERN_NOT_SET",[])
}var S=I(T);
var R;
try{R=new RegExp(S)
}catch(V){throw N.csv.getMessage(W,"REGEX_VALIDATOR_MATCH_EXCEPTION",[])
}if(!R.test(U)){throw N.csv.interpolateMessage(W,[T,Q])
}};
var I=function(Q){if(!(Q.slice(0,1)==="^")){Q="^"+Q
}if(!(Q.slice(-1)==="$")){Q=Q;
+"$"
}return Q
};
F.extend(N.csv,{validateLongRange:function(S,Q,U,T){var R=typeof S;
if(R!=="number"){if(R!="string"){throw N.csv.getMessage(T,"LONG_RANGE_VALIDATOR_TYPE",[componentId,""])
}else{S=F.trim(S);
if(!N.csv.RE_DIGITS.test(S)||(S=parseInt(S,10))==NaN){throw N.csv.getMessage(T,"LONG_RANGE_VALIDATOR_TYPE",[componentId,""])
}}}O(S,Q,U,T)
},validateDoubleRange:function(S,Q,U,T){var R=typeof S;
if(R!=="number"){if(R!=="string"){throw N.csv.getMessage(T,"DOUBLE_RANGE_VALIDATOR_TYPE",[componentId,""])
}else{S=F.trim(S);
if(!N.csv.RE_FLOAT.test(S)||(S=parseFloat(S))==NaN){throw N.csv.getMessage(T,"DOUBLE_RANGE_VALIDATOR_TYPE",[componentId,""])
}}}O(S,Q,U,T)
},validateLength:function(S,Q,U,T){var R=S?S.length:0;
O(R,Q,U,T)
},validateSize:function(S,Q,U,T){var R=S?S.length:0;
O(R,Q,U,T)
},validateRegex:function(R,Q,T,S){C(R,Q,T.pattern,S)
},validatePattern:function(R,Q,T,S){C(R,Q,T.regexp,S)
},validateRequired:function(R,Q,T,S){if(undefined===R||null===R||""===R){throw N.csv.interpolateMessage(S,[Q])
}},validateTrue:function(R,Q,T,S){if(R!==true){throw S
}},validateFalse:function(R,Q,T,S){if(R!==false){throw S
}},validateMax:function(R,Q,T,S){if(R>T.value){throw S
}},validateMin:function(R,Q,T,S){if(R<T.value){throw S
}}})
})(jQuery,window.RichFaces||(window.RichFaces={}));
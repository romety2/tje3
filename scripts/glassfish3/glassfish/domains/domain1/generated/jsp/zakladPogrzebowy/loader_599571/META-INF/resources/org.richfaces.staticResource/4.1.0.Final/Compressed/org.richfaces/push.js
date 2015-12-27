(function(H,D,E){var A="Push";
var G=D.Event.RICH_NAMESPACE;
var K=D.Event.EVENT_NAMESPACE_SEPARATOR;
var B="dataAvailable"+K+G+K+A;
var L="error"+K+G+K+A;
var C=function(M){return B+K+M
};
var I=function(M){return L+K+M
};
D.Push=(function(){var N={};
var P={};
var W={};
var Q=null;
var V=null;
var O=null;
var M=/^(<!--[^>]+-->\s*)+/;
var R=/<([^>]*)>/g;
var U=-1;
var Y=function(a){var Z=a;
if(a.charAt(0)=="/"){Z=location.protocol+"//"+location.host+a
}return Z
};
var T=function(Z){var a=Z.responseBody.replace(M,"");
if(a){var c;
while(c=R.exec(a)){if(!c[1]){continue
}var b=E.parseJSON("{"+c[1]+"}");
if(b.number<=U){continue
}D.Event.fire(document,C(b.topic),b.data);
U=b.number
}}jQuery.atmosphere.request.requestCount=0
};
var X=function(){var Z=function(f){var e=E.parseJSON(f);
for(var d in e.failures){D.Event.fire(document,I(d),e.failures[d])
}if(e.sessionId){O=e.sessionId;
E.atmosphere.subscribe((V||Q)+"?__richfacesPushAsync=1&pushSessionId="+O,T,{transport:D.Push.transport,fallbackTransport:D.Push.fallbackTransport})
}};
var c=new Array();
for(var a in W){c.push(a)
}var b={pushTopic:c};
if(O){b.forgetPushSessionId=O
}E.ajax({data:b,dataType:"text",success:Z,traditional:true,type:"POST",url:Q})
};
var S=function(){E.atmosphere.closeSuspendedConnection()
};
return{increaseSubscriptionCounters:function(Z){if(isNaN(W[Z]++)){W[Z]=1;
N[Z]=true
}},decreaseSubscriptionCounters:function(Z){if(--W[Z]==0){delete W[Z];
P[Z]=true
}},setPushResourceUrl:function(Z){Q=Y(Z)
},setPushHandlerUrl:function(Z){V=Y(Z)
},updateConnection:function(){if(E.isEmptyObject(W)){S()
}else{if(!E.isEmptyObject(N)||!E.isEmptyObject(P)){S();
X()
}}N={};
P={}
}}
}());
E(document).ready(D.Push.updateConnection);
D.Push.transport="long-polling";
D.Push.fallbackTransport=undefined;
var F=function(M){if(M.type=="event"){if(M.status!="success"){return 
}}else{if(M.type!="error"){return 
}}D.Push.updateConnection()
};
H.ajax.addOnEvent(F);
H.ajax.addOnError(F);
D.ui=D.ui||{};
D.ui.Push=D.BaseComponent.extendClass({name:A,init:function(N,M){J.constructor.call(this,N);
this.attachToDom();
this.__address=M.address;
this.__handlers={};
if(M.ondataavailable){this.__bindDataHandler(M.ondataavailable)
}if(M.onerror){this.__bindErrorHandler(M.onerror)
}D.Push.increaseSubscriptionCounters(this.__address)
},__bindDataHandler:function(N){var M=C(this.__address);
this.__handlers.data=D.Event.bind(document,M,$.proxy(N,document.getElementById(this.id)),this)
},__unbindDataHandler:function(){if(this.__handlers.data){var M=C(this.__address);
D.Event.unbind(document,M,this.__handlers.data);
this.__handlers.data=null
}},__bindErrorHandler:function(N){var M=I(this.__address);
this.__handlers.error=D.Event.bind(document,M,$.proxy(N,document.getElementById(this.id)),this)
},__unbindErrorHandler:function(){if(this.__handlers.error){var M=I(this.__address);
D.Event.unbind(document,M,this.__handlers.error);
this.__handlers.error=null
}},destroy:function(){this.__unbindDataHandler();
this.__unbindErrorHandler();
D.Push.decreaseSubscriptionCounters(this.__address);
J.destroy.call(this)
}});
var J=D.ui.Push.$super
}(jsf,window.RichFaces,jQuery));
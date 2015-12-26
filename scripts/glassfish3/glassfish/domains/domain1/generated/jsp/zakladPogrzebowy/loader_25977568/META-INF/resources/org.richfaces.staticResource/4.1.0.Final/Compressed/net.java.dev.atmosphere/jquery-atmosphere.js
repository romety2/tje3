jQuery.atmosphere=function(){var A;
jQuery(window).unload(function(){if(A){A.abort()
}if(!(typeof (transferDoc)=="undefined")){if(transferDoc!=null){transferDoc=null;
CollectGarbage()
}}});
return{version:0.8,response:{status:200,responseBody:"",headers:[],state:"messageReceived",transport:"polling",push:[],error:null,id:0},request:{},abordingConnection:false,logLevel:"info",callbacks:[],activeTransport:null,websocket:null,killHiddenIFrame:null,uuid:0,opening:true,subscribe:function(B,D,C){jQuery.atmosphere.request=jQuery.extend({timeout:300000,method:"GET",headers:{},contentType:"",cache:true,async:true,ifModified:false,callback:null,dataType:"",url:B,data:"",suspend:true,maxRequest:60,maxStreamingLength:10000000,lastIndex:0,logLevel:"info",requestCount:0,fallbackMethod:"GET",fallbackTransport:"streaming",transport:"long-polling",webSocketImpl:null},C);
logLevel=jQuery.atmosphere.request.logLevel;
if(D!=null){jQuery.atmosphere.addCallback(D);
jQuery.atmosphere.request.callback=D
}if(jQuery.atmosphere.request.transport!=jQuery.atmosphere.activeTransport){jQuery.atmosphere.closeSuspendedConnection()
}jQuery.atmosphere.activeTransport=jQuery.atmosphere.request.transport;
jQuery.atmosphere.uuid=jQuery.atmosphere.guid();
if(jQuery.atmosphere.request.transport!="websocket"){jQuery.atmosphere.executeRequest()
}else{if(jQuery.atmosphere.request.transport=="websocket"){if(jQuery.atmosphere.request.webSocketImpl==null&&!window.WebSocket&&!window.MozWebSocket){jQuery.atmosphere.log(logLevel,["Websocket is not supported, using request.fallbackTransport ("+jQuery.atmosphere.request.fallbackTransport+")"]);
jQuery.atmosphere.request.transport=jQuery.atmosphere.request.fallbackTransport;
jQuery.atmosphere.response.transport=jQuery.atmosphere.request.fallbackTransport;
jQuery.atmosphere.executeRequest()
}else{jQuery.atmosphere.executeWebSocket()
}}}},closeSuspendedConnection:function(){jQuery.atmosphere.abordingConnection=true;
if(A!=null){A.abort()
}if(jQuery.atmosphere.websocket!=null){jQuery.atmosphere.websocket.close();
jQuery.atmosphere.websocket=null
}jQuery.atmosphere.abordingConnection=false;
if(!(typeof (transferDoc)=="undefined")){if(transferDoc!=null){transferDoc=null;
CollectGarbage()
}}},executeRequest:function(){if(jQuery.atmosphere.request.transport=="streaming"){if(jQuery.browser.msie){jQuery.atmosphere.ieStreaming();
return 
}else{if(jQuery.browser.opera){jQuery.atmosphere.operaStreaming();
return 
}}}if(jQuery.atmosphere.request.requestCount++<jQuery.atmosphere.request.maxRequest){jQuery.atmosphere.response.push=function(I){jQuery.atmosphere.request.callback=null;
jQuery.atmosphere.publish(I,null,jQuery.atmosphere.request)
};
var G=jQuery.atmosphere.request;
var B=jQuery.atmosphere.response;
if(G.transport!="polling"){B.transport=G.transport
}var F;
var D=false;
if(jQuery.browser.msie){var C=["Msxml2.XMLHTTP","Microsoft.XMLHTTP"];
for(var E=0;
E<C.length;
E++){try{F=new ActiveXObject(C[E])
}catch(H){}}}else{if(window.XMLHttpRequest){F=new XMLHttpRequest()
}}if(G.suspend){A=F
}jQuery.atmosphere.doRequest(F,G);
if(!jQuery.browser.msie){F.onerror=function(){D=true;
try{B.status=XMLHttpRequest.status
}catch(I){B.status=404
}B.state="error";
jQuery.atmosphere.invokeCallback(B);
F.abort();
A=null
}
}F.onreadystatechange=function(){if(jQuery.atmosphere.abordingConnection){return 
}var S=false;
var N=false;
if(F.readyState==4){jQuery.atmosphere.request=G;
if(G.suspend&&F.status==200&&G.transport!="streaming"){jQuery.atmosphere.executeRequest()
}if(jQuery.browser.msie){N=true
}}else{if(!jQuery.browser.msie&&F.readyState==3&&F.status==200){N=true
}else{clearTimeout(G.id)
}}if(N){var Q=F.responseText;
this.previousLastIndex=G.lastIndex;
if(G.transport=="streaming"){B.responseBody=Q.substring(G.lastIndex,Q.length);
B.isJunkEnded=true;
if(G.lastIndex==0&&B.responseBody.indexOf("<!-- Welcome to the Atmosphere Framework.")!=-1){B.isJunkEnded=false
}if(!B.isJunkEnded){var R="<!-- EOD -->";
var K=R.length;
var M=B.responseBody.indexOf(R)+K;
if(M>K&&M!=B.responseBody.length){B.responseBody=B.responseBody.substring(M)
}else{S=true
}}else{B.responseBody=Q.substring(G.lastIndex,Q.length)
}G.lastIndex=Q.length;
if(S){return 
}}else{B.responseBody=Q;
G.lastIndex=Q.length
}try{B.status=F.status;
B.headers=F.getAllResponseHeaders()
}catch(P){B.status=404
}if(G.suspend){B.state="messageReceived"
}else{B.state="messagePublished"
}if(B.responseBody.indexOf("parent.callback")!=-1){var O=0;
var J=B.responseBody;
while(J.indexOf("('",O)!=-1){var I=J.indexOf("('",O)+2;
var L=J.indexOf("')",O);
if(L<0){G.lastIndex=this.previousLastIndex;
return 
}B.responseBody=J.substring(I,L);
O=L+2;
jQuery.atmosphere.invokeCallback(B);
if((G.transport=="streaming")&&(Q.length>jQuery.atmosphere.request.maxStreamingLength)){F.abort();
jQuery.atmosphere.doRequest(F,G)
}}}else{jQuery.atmosphere.invokeCallback(B)
}}};
F.send(G.data);
if(G.suspend){G.id=setTimeout(function(){F.abort();
jQuery.atmosphere.subscribe(G.url,null,G)
},G.timeout)
}}else{jQuery.atmosphere.log(logLevel,["Max re-connection reached."])
}},doRequest:function(C,D){C.open(D.method,D.url,true);
C.setRequestHeader("X-Atmosphere-Framework",jQuery.atmosphere.version);
C.setRequestHeader("X-Atmosphere-Transport",D.transport);
C.setRequestHeader("X-Cache-Date",new Date().getTime());
if(jQuery.atmosphere.request.contentType!=""){C.setRequestHeader("Content-Type",jQuery.atmosphere.request.contentType)
}C.setRequestHeader("X-Atmosphere-tracking-id",jQuery.atmosphere.uuid);
for(var B in D.headers){C.setRequestHeader(B,D.headers[B])
}},operaStreaming:function(){jQuery.atmosphere.closeSuspendedConnection();
var B=jQuery.atmosphere.request.url;
var D=jQuery.atmosphere.request.callback;
jQuery.atmosphere.response.push=function(E){jQuery.atmosphere.request.transport="polling";
jQuery.atmosphere.request.callback=null;
jQuery.atmosphere.publish(E,null,jQuery.atmosphere.request)
};
function C(){var E=document.createElement("iframe");
E.style.width="0px";
E.style.height="0px";
E.style.border="0px";
E.id="__atmosphere";
document.body.appendChild(E);
var F;
if(E.contentWindow){F=E.contentWindow.document
}else{if(E.document){F=E.document
}else{if(E.contentDocument){F=E.contentDocument
}}}if(/\?/i.test(B)){B+="&"
}else{B+="?"
}B+="callback=jquery.atmosphere.streamingCallback";
E.src=B
}C()
},ieStreaming:function(){if(!(typeof (transferDoc)=="undefined")){if(transferDoc!=null){transferDoc=null;
CollectGarbage()
}}var B=jQuery.atmosphere.request.url;
jQuery.atmosphere.response.push=function(D){jQuery.atmosphere.request.transport="polling";
jQuery.atmosphere.request.callback=null;
jQuery.atmosphere.publish(D,null,jQuery.atmosphere.request)
};
transferDoc=new ActiveXObject("htmlfile");
transferDoc.open();
transferDoc.close();
var C=transferDoc.createElement("div");
transferDoc.body.appendChild(C);
C.innerHTML="<iframe src='"+B+"'></iframe>";
transferDoc.parentWindow.callback=jQuery.atmosphere.streamingCallback
},streamingCallback:function(C){var B=jQuery.atmosphere.response;
B.transport="streaming";
B.status=200;
B.responseBody=C;
B.state="messageReceived";
jQuery.atmosphere.invokeCallback(B)
},executeWebSocket:function(){var F=jQuery.atmosphere.request;
var E=false;
jQuery.atmosphere.log(logLevel,["Invoking executeWebSocket"]);
jQuery.atmosphere.response.transport="websocket";
var C=jQuery.atmosphere.request.url;
var G=jQuery.atmosphere.request.callback;
if(C.indexOf("http")==-1&&C.indexOf("ws")==-1){C=jQuery.atmosphere.parseUri(document.location,C);
jQuery.atmosphere.debug("Using URL: "+C)
}var B=C.replace("http:","ws:").replace("https:","wss:");
var D=null;
if(jQuery.atmosphere.request.webSocketImpl!=null){D=jQuery.atmosphere.request.webSocketImpl
}else{if(window.WebSocket){D=new WebSocket(B)
}else{D=new MozWebSocket(B)
}}jQuery.atmosphere.websocket=D;
jQuery.atmosphere.response.push=function(H){var I;
try{I=jQuery.atmosphere.request.data;
D.send(jQuery.atmosphere.request.data)
}catch(J){jQuery.atmosphere.log(logLevel,["Websocket failed. Downgrading to Comet and resending "+I]);
F.transport=F.fallbackTransport;
F.method=F.fallbackMethod;
F.data=I;
jQuery.atmosphere.response.transport=F.fallbackTransport;
jQuery.atmosphere.request=F;
jQuery.atmosphere.executeRequest();
D.onclose=function(K){};
D.close()
}};
D.onopen=function(H){jQuery.atmosphere.debug("Websocket successfully opened");
E=true;
jQuery.atmosphere.response.state="opening";
jQuery.atmosphere.invokeCallback(jQuery.atmosphere.response)
};
D.onmessage=function(I){var J=I.data;
if(J.indexOf("parent.callback")!=-1){var K=J.indexOf("('")+2;
var H=J.indexOf("')");
jQuery.atmosphere.response.responseBody=J.substring(K,H)
}else{jQuery.atmosphere.response.responseBody=J
}jQuery.atmosphere.invokeCallback(jQuery.atmosphere.response)
};
D.onerror=function(H){jQuery.atmosphere.warn("Websocket error, reason: "+H.reason);
jQuery.atmosphere.response.state="error";
jQuery.atmosphere.invokeCallback(jQuery.atmosphere.response)
};
D.onclose=function(H){if(!E||!H.wasClean){var I=jQuery.atmosphere.request.data;
jQuery.atmosphere.log(logLevel,["Websocket failed. Downgrading to Comet and resending "+I]);
F.transport=F.fallbackTransport;
F.method=F.fallbackMethod;
F.data=I;
jQuery.atmosphere.response.transport=F.fallbackTransport;
jQuery.atmosphere.request=F;
jQuery.atmosphere.executeRequest()
}else{jQuery.atmosphere.debug("Websocket closed cleanly");
jQuery.atmosphere.response.state="closed";
jQuery.atmosphere.invokeCallback(jQuery.atmosphere.response)
}}
},addCallback:function(B){if(jQuery.inArray(B,jQuery.atmosphere.callbacks)==-1){jQuery.atmosphere.callbacks.push(B)
}},removeCallback:function(C){var B=jQuery.inArray(C,jQuery.atmosphere.callbacks);
if(B!=-1){jQuery.atmosphere.callbacks.splice(B)
}},invokeCallback:function(B){var C=function(D,E){E(B)
};
jQuery.atmosphere.log(logLevel,["Invoking "+jQuery.atmosphere.callbacks.length+" callbacks"]);
if(jQuery.atmosphere.callbacks.length>0){jQuery.each(jQuery.atmosphere.callbacks,C)
}},publish:function(B,D,C){jQuery.atmosphere.request=jQuery.extend({connected:false,timeout:60000,method:"POST",contentType:"",headers:{},cache:true,async:true,ifModified:false,callback:null,dataType:"",url:B,data:"",suspend:false,maxRequest:60,logLevel:"info",requestCount:0,transport:"polling"},C);
if(D!=null){jQuery.atmosphere.addCallback(D)
}jQuery.atmosphere.request.transport="polling";
if(jQuery.atmosphere.request.transport!="websocket"){jQuery.atmosphere.executeRequest()
}else{if(jQuery.atmosphere.request.transport=="websocket"){if(!window.WebSocket&&!window.MozWebSocket){alert("WebSocket not supported by this browser")
}else{jQuery.atmosphere.executeWebSocket()
}}}},unload:function(B){if(window.addEventListener){document.addEventListener("unload",B,false);
window.addEventListener("unload",B,false)
}else{document.attachEvent("onunload",B);
window.attachEvent("onunload",B)
}},kill_load_bar:function(){if(jQuery.atmosphere.killHiddenIFrame==null){jQuery.atmosphere.killHiddenIFrame=document.createElement("iframe");
var B=jQuery.atmosphere.killHiddenIFrame;
B.style.display="block";
B.style.width="0";
B.style.height="0";
B.style.border="0";
B.style.margin="0";
B.style.padding="0";
B.style.overflow="hidden";
B.style.visibility="hidden"
}document.body.appendChild(B);
B.src="about:blank";
document.body.removeChild(B)
},log:function(D,C){if(window.console){var B=window.console[D];
if(typeof B=="function"){B.apply(window.console,C)
}}},warn:function(){jQuery.atmosphere.log("warn",arguments)
},info:function(){if(logLevel!="warn"){jQuery.atmosphere.log("info",arguments)
}},debug:function(){if(logLevel=="debug"){jQuery.atmosphere.log("debug",arguments)
}},close:function(){jQuery.atmosphere.closeSuspendedConnection()
},S4:function(){return(((1+Math.random())*65536)|0).toString(16).substring(1)
},guid:function(){return(jQuery.atmosphere.S4()+jQuery.atmosphere.S4()+"-"+jQuery.atmosphere.S4()+"-"+jQuery.atmosphere.S4()+"-"+jQuery.atmosphere.S4()+"-"+jQuery.atmosphere.S4()+jQuery.atmosphere.S4()+jQuery.atmosphere.S4())
},parseUri:function(H,D){var M=window.location.protocol;
var N=window.location.host;
var O=window.location.pathname;
var L={};
var G="";
var I;
if((I=D.search(/\:/))>=0){M=D.substring(0,I+1);
D=D.substring(I+1)
}if((I=D.search(/\#/))>=0){G=D.substring(I+1);
D=D.substring(0,I)
}if((I=D.search(/\?/))>=0){var J=D.substring(I+1)+"&;";
D=D.substring(0,I);
while((I=J.search(/\&/))>=0){var E=J.substring(0,I);
J=J.substring(I+1);
if(E.length){var F=E.search(/\=/);
if(F<0){L[E]=""
}else{L[E.substring(0,F)]=decodeURIComponent(E.substring(F+1))
}}}}if(D.search(/\/\//)==0){D=D.substring(2);
if((I=D.search(/\//))>=0){N=D.substring(0,I);
O=D.substring(I)
}else{N=D;
O="/"
}}else{if(D.search(/\//)==0){O=D
}else{var C=O.lastIndexOf("/");
if(C<0){O="/"
}else{if(C<O.length-1){O=O.substring(0,C+1)
}}while(D.search(/\.\.\//)==0){var C=O.lastIndexOf("/",O.lastIndexOf("/")-1);
if(C>=0){O=O.substring(0,C+1)
}D=D.substring(3)
}O=O+D
}}var D=M+"//"+N+O;
var B="?";
for(var K in L){D+=B+K+"="+encodeURIComponent(L[K]);
B="&"
}return D
}}
}();
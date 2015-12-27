(function(C,A){A.Event=A.Event||{};
var D=jsf.ajax.request;
jsf.ajax.request=function B(I,H,E){var F,G;
if(typeof I==="string"){F=document.getElementById(I)
}else{if(typeof I==="object"){F=I
}else{throw new Error("jsf.request: source must be object or string")
}}if(C(F).is("form")){G=I
}else{G=C("form").has(F).get(0)
}if(G&&A.Event&&A.Event.callHandler){A.Event.callHandler(G,"ajaxsubmit")
}D(I,H,E)
}
})(jQuery,window.RichFaces||(window.RichFaces={}));
(function(E,D){D.ui=D.ui||{};
var B={toolbar:"Basic",skin:"richfaces",readonly:false,style:"",styleClass:"",editorStyle:"",editorClass:"",width:"100%",height:"200px"};
var A={customConfig:""};
var C=["key","paste","undo","redo"];
D.ui.Editor=function(I,H,G){F.constructor.call(this,I);
this.options=E.extend({},B,H);
this.componentId=I;
this.textareaId=I+":inp";
this.editorElementId="cke_"+this.textareaId;
this.valueChanged=false;
this.dirtyState=false;
this.config=E.extend({},A,G);
this.attachToDom(this.componentId);
E(document).ready(E.proxy(this.__initializationHandler,this));
D.Event.bindById(this.__getTextarea(),"init",this.options.oninit,this);
D.Event.bindById(this.__getTextarea(),"dirty",this.options.ondirty,this)
};
D.BaseComponent.extend(D.ui.Editor);
var F=D.ui.Editor.$super;
E.extend(D.ui.Editor.prototype,{name:"Editor",__initializationHandler:function(){this.ckeditor=CKEDITOR.replace(this.textareaId,this.__getConfiguration());
if(this.__getForm()){this.__updateTextareaHandlerWrapper=D.Event.bind(this.__getForm(),"ajaxsubmit",E.proxy(this.__updateTextareaHandler,this))
}this.ckeditor.on("instanceReady",E.proxy(this.__instanceReadyHandler,this));
this.ckeditor.on("blur",E.proxy(this.__blurHandler,this));
this.ckeditor.on("focus",E.proxy(this.__focusHandler,this));
for(var G in C){this.ckeditor.on(C[G],E.proxy(this.__checkDirtyHandlerWithDelay,this))
}this.dirtyCheckingInterval=window.setInterval(E.proxy(this.__checkDirtyHandler,this),100)
},__checkDirtyHandlerWithDelay:function(){window.setTimeout(E.proxy(this.__checkDirtyHandler,this),0)
},__checkDirtyHandler:function(){if(this.ckeditor.checkDirty()){this.dirtyState=true;
this.valueChanged=true;
this.ckeditor.resetDirty();
this.__dirtyHandler()
}},__dirtyHandler:function(){this.invokeEvent.call(this,"dirty",document.getElementById(this.textareaId))
},__updateTextareaHandler:function(){this.ckeditor.updateElement()
},__instanceReadyHandler:function(G){this.__setupStyling();
this.__setupPassThroughAttributes();
this.invokeEvent.call(this,"init",document.getElementById(this.textareaId),G)
},__blurHandler:function(G){this.invokeEvent.call(this,"blur",document.getElementById(this.textareaId),G);
if(this.isDirty()){this.valueChanged=true;
this.__changeHandler()
}this.dirtyState=false
},__focusHandler:function(G){this.invokeEvent.call(this,"focus",document.getElementById(this.textareaId),G)
},__changeHandler:function(G){this.invokeEvent.call(this,"change",document.getElementById(this.textareaId),G)
},__getTextarea:function(){return E(document.getElementById(this.textareaId))
},__getForm:function(){return E("form").has(this.__getTextarea()).get(0)
},__getConfiguration:function(){var G=this.__getTextarea();
return E.extend({skin:this.options.skin,toolbar:this.__getToolbar(),readOnly:G.attr("readonly")||this.options.readonly,width:this.__resolveUnits(this.options.width),height:this.__resolveUnits(this.options.height),bodyClass:"rf-ed-b",defaultLanguage:this.options.lang,contentsLanguage:this.options.lang},this.config)
},__setupStyling:function(){var I=E(document.getElementById(this.editorElementId));
if(!I.hasClass("rf-ed")){I.addClass("rf-ed")
}var G=E.trim(this.options.styleClass+" "+this.options.editorClass);
if(this.initialStyle==undefined){this.initialStyle=I.attr("style")
}var H=this.__concatStyles(this.initialStyle,this.options.style,this.options.editorStyle);
if(this.oldStyleClass!==G){if(this.oldStyleClass){I.removeClass(this.oldStyleClass)
}I.addClass(G);
this.oldStyleClass=G
}if(this.oldStyle!==H){I.attr("style",H);
this.oldStyle=H
}},__setupPassThroughAttributes:function(){var G=this.__getTextarea();
var H=E(document.getElementById(this.editorElementId));
H.attr("title",G.attr("title"))
},__concatStyles:function(){var G="";
for(var H=0;
H<arguments.length;
H++){var I=E.trim(arguments[H]);
if(I){G=G+I+"; "
}}return G
},__getToolbar:function(){var H=this.options.toolbar;
var G=H.toLowerCase();
if(G==="basic"){return"Basic"
}if(G==="full"){return"Full"
}return H
},__setOptions:function(G){this.options=E.extend({},B,G)
},__resolveUnits:function(G){var G=E.trim(G);
if(G.match(/^[0-9]+$/)){return G+"px"
}else{return G
}},getEditor:function(){return this.ckeditor
},setValue:function(G){this.ckeditor.setData(G,E.proxy(function(){this.valueChanged=false;
this.dirtyState=false;
this.ckeditor.resetDirty()
},this))
},getValue:function(){return this.ckeditor.getData()
},getInput:function(){return document.getElementById(this.textareaId)
},focus:function(){this.ckeditor.focus()
},blur:function(){this.ckeditor.focusManager.forceBlur()
},isFocused:function(){return this.ckeditor.focusManager.hasFocus
},isDirty:function(){return this.dirtyState||this.ckeditor.checkDirty()
},isValueChanged:function(){return this.valueChanged||this.isDirty()
},setReadOnly:function(G){this.ckeditor.setReadOnly(G!==false)
},isReadOnly:function(){return this.ckeditor.readOnly
},destroy:function(){window.clearInterval(this.dirtyCheckingInterval);
if(this.__getForm()){D.Event.unbind(this.__getForm(),"ajaxsubmit",this.__updateTextareaHandlerWrapper)
}if(this.ckeditor){this.ckeditor.destroy();
this.ckeditor=null
}this.__getTextarea().show();
F.destroy.call(this)
}})
})(jQuery,RichFaces);
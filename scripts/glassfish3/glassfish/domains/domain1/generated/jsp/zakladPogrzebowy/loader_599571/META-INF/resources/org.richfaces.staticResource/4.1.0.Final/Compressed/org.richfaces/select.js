(function(D,C){C.ui=C.ui||{};
C.ui.Select=function(K,G){this.id=K;
var J=D.extend({},B,G);
J.attachTo=K;
J.scrollContainer=D(document.getElementById(K+"Items")).parent()[0];
J.focusKeeperEnabled=false;
E.constructor.call(this,K,J);
this.options=J;
this.defaultLabel=J.defaultLabel;
var I=this.__getValue();
this.initialValue=(I!=this.defaultLabel)?I:"";
this.selValueInput=D(document.getElementById(K+"selValue"));
this.container=this.selValueInput.parent();
this.clientSelectItems=J.clientSelectItems;
this.filterFunction=J.filterFunction;
if(J.showControl&&!J.disabled){this.container.bind("mousedown",D.proxy(this.__onBtnMouseDown,this)).bind("mouseup",D.proxy(this.__onMouseUp,this))
}this.selectFirst=J.selectFirst;
this.popupList=new C.ui.PopupList((K+"List"),this,J);
this.list=this.popupList.__getList();
this.listElem=D(document.getElementById(K+"List"));
this.listElem.bind("mousedown",D.proxy(this.__onListMouseDown,this));
this.listElem.bind("mouseup",D.proxy(this.__onMouseUp,this));
var H={};
H["listshow"+this.namespace]=D.proxy(this.__listshowHandler,this);
H["listhide"+this.namespace]=D.proxy(this.__listhideHandler,this);
C.Event.bind(this.input,H,this);
this.originalItems=this.list.__getItems();
this.enableManualInput=J.enableManualInput;
if(this.originalItems.length>0&&this.enableManualInput){this.cache=new C.utils.Cache("",this.originalItems,A,true)
}this.changeDelay=J.changeDelay
};
C.ui.InputBase.extend(C.ui.Select);
var E=C.ui.Select.$super;
var B={defaultLabel:"",selectFirst:true,showControl:true,enableManualInput:false,itemCss:"rf-sel-opt",selectItemCss:"rf-sel-sel",listCss:"rf-sel-lst-cord",changeDelay:8,disabled:false,filterFunction:undefined};
var F=/^[\n\s]*(.*)[\n\s]*$/;
var A=function(G){var H=[];
G.each(function(){H.push(D(this).text().replace(F,"$1"))
});
return H
};
D.extend(C.ui.Select.prototype,(function(){return{name:"select",defaultLabelClass:"rf-sel-dflt-lbl",__listshowHandler:function(G){},__listhideHandler:function(G){},__onBtnMouseDown:function(G){if(!this.popupList.isVisible()){this.__updateItems();
this.__showPopup()
}else{this.__hidePopup()
}this.isMouseDown=true
},__focusHandler:function(G){if(!this.focused){if(this.__getValue()==this.defaultLabel){this.__setValue("")
}this.focusValue=this.selValueInput.val();
this.focused=true;
this.invokeEvent.call(this,"focus",document.getElementById(this.id),G)
}},__keydownHandler:function(H){var G;
if(H.keyCode){G=H.keyCode
}else{if(H.which){G=H.which
}}var I=this.popupList.isVisible();
switch(G){case C.KEYS.DOWN:H.preventDefault();
if(!I){this.__updateItems();
this.__showPopup()
}else{this.list.__selectNext()
}break;
case C.KEYS.UP:H.preventDefault();
if(I){this.list.__selectPrev()
}break;
case C.KEYS.RETURN:H.preventDefault();
if(I){this.list.__selectCurrent()
}return false;
break;
case C.KEYS.TAB:break;
case C.KEYS.ESC:H.preventDefault();
if(I){this.__hidePopup()
}break;
default:var J=this;
window.clearTimeout(this.changeTimerId);
this.changeTimerId=window.setTimeout(function(){J.__onChangeValue(H)
},this.changeDelay);
break
}},__onChangeValue:function(H){this.list.__selectByIndex();
var G=this.__getValue();
if(this.cache&&this.cache.isCached(G)){this.__updateItems();
if(this.list.__getItems().length!=0){this.container.removeClass("rf-sel-fld-err")
}else{this.container.addClass("rf-sel-fld-err")
}if(!this.popupList.isVisible()){this.__showPopup()
}}},__blurHandler:function(H){if(!this.isMouseDown){var G=this;
this.timeoutId=window.setTimeout(function(){if(G.input!==null){G.onblur(H)
}},200)
}else{this.__setInputFocus();
this.isMouseDown=false
}},__onListMouseDown:function(G){this.isMouseDown=true
},__onMouseUp:function(G){this.isMouseDown=false;
this.__setInputFocus()
},__updateItems:function(){var G=this.__getValue();
G=(G!=this.defaultLabel)?G:"";
this.__updateItemsFromCache(G);
if(this.selectFirst){this.list.__selectByIndex(0)
}},__updateItemsFromCache:function(I){if(this.originalItems.length>0&&this.enableManualInput){var H=this.cache.getItems(I,this.filterFunction);
var G=D(H);
this.list.__setItems(G);
D(document.getElementById(this.id+"Items")).empty().append(G)
}},__getClientItemFromCache:function(J){var I;
var H;
if(this.enableManualInput){var G=this.cache.getItems(J,this.filterFunction);
if(G&&G.length>0){var L=D(G[0]);
D.each(this.clientSelectItems,function(){if(this.id==L.attr("id")){H=this.label;
I=this.value;
return false
}})
}else{this.container.removeClass("rf-sel-fld-err");
var K=this.selValueInput.val();
if(K&&K!=""){D.each(this.clientSelectItems,function(){if(this.value==K){H=this.label;
I=this.value;
return false
}})
}}}if(H&&I){return{label:H,value:I}
}},__getClientItem:function(I){var H;
var G=I;
D.each(this.clientSelectItems,function(){if(G==this.label){H=this.value
}});
if(G&&H){return{label:G,value:H}
}},__showPopup:function(){this.popupList.show();
this.invokeEvent.call(this,"listshow",document.getElementById(this.id))
},__hidePopup:function(){this.popupList.hide();
this.invokeEvent.call(this,"listhide",document.getElementById(this.id))
},showPopup:function(){if(!this.popupList.isVisible()){this.__updateItems();
this.__showPopup()
}this.__setInputFocus();
if(!this.focused){if(this.__getValue()==this.defaultLabel){this.__setValue("")
}this.focusValue=this.selValueInput.val();
this.focused=true;
this.invokeEvent.call(this,"focus",document.getElementById(this.id))
}},hidePopup:function(){if(this.popupList.isVisible()){this.__hidePopup();
var G=this.__getValue();
if(!G||G==""){this.__setValue(this.defaultLabel);
this.selValueInput.val("")
}this.focused=false;
this.invokeEvent.call(this,"blur",document.getElementById(this.id));
if(this.focusValue!=this.selValueInput.val()){this.invokeEvent.call(this,"change",document.getElementById(this.id))
}}},processItem:function(I){var H=D(I).attr("id");
var G;
D.each(this.clientSelectItems,function(){if(this.id==H){G=this.label;
return false
}});
this.__setValue(G);
this.__hidePopup();
this.__setInputFocus();
this.__save();
this.invokeEvent.call(this,"selectitem",document.getElementById(this.id))
},__save:function(){var I="";
var G="";
var H=this.__getValue();
var J;
if(H&&H!=""){if(this.enableManualInput){J=this.__getClientItemFromCache(H)
}else{J=this.__getClientItem(H)
}if(J){G=J.label;
I=J.value
}}this.__setValue(G);
this.selValueInput.val(I)
},onblur:function(H){this.__hidePopup();
var G=this.__getValue();
if(!G||G==""){this.__setValue(this.defaultLabel);
this.selValueInput.val("")
}this.focused=false;
this.invokeEvent.call(this,"blur",document.getElementById(this.id),H);
if(this.focusValue!=this.selValueInput.val()){this.invokeEvent.call(this,"change",document.getElementById(this.id),H)
}},getValue:function(){return this.selValueInput.val()
},setValue:function(I){if(I==null||I==""){this.__setValue("");
this.__save();
this.__updateItems();
return 
}var H;
for(var G=0;
G<this.clientSelectItems.length;
G++){H=this.clientSelectItems[G];
if(H.value==I){this.__setValue(H.label);
this.__save();
this.list.__selectByIndex(G);
return 
}}},getLabel:function(){return this.__getValue()
},destroy:function(){this.popupList.destroy();
this.popupList=null;
E.destroy.call(this)
}}
})())
})(jQuery,window.RichFaces);
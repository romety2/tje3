(function(G,J){J.ui=J.ui||{};
J.ui.List=function(N,K){I.constructor.call(this,N);
this.namespace=this.namespace||"."+J.Event.createNamespace(this.name,this.id);
this.attachToDom();
var M=G.extend({},F,K);
this.list=G(document.getElementById(N));
this.selectListener=M.selectListener;
this.selectItemCss=M.selectItemCss;
this.selectItemCssMarker=M.selectItemCss.split(" ",1)[0];
this.scrollContainer=G(M.scrollContainer);
this.itemCss=M.itemCss.split(" ",1)[0];
this.listCss=M.listCss;
this.clickRequiredToSelect=M.clickRequiredToSelect;
this.index=-1;
this.disabled=M.disabled;
this.focusKeeper=G(document.getElementById(N+"FocusKeeper"));
this.focusKeeper.focused=false;
this.lastMouseX=null;
this.lastMouseY=null;
this.isMouseDown=false;
this.list.bind("mousedown",G.proxy(this.__onMouseDown,this)).bind("mouseup",G.proxy(this.__onMouseUp,this));
C.call(this);
if(M.focusKeeperEnabled){B.call(this)
}this.__updateItemsList();
if(M.clientSelectItems!==null){var L=[];
G.each(M.clientSelectItems,function(O){L[this.id]=this
});
this.__storeClientSelectItems(this.items,L)
}};
J.BaseComponent.extend(J.ui.List);
var I=J.ui.List.$super;
var F={clickRequiredToSelect:false,disabled:false,selectListener:false,clientSelectItems:null,focusKeeperEnabled:true};
var C=function(){var K={};
K["click"+this.namespace]=G.proxy(this.onClick,this);
K["dblclick"+this.namespace]=G.proxy(this.onDblclick,this);
K["mouseover"+this.namespace]=H;
if(!G.browser.msie&&!G.browser.opera){K["mouseenter"+this.namespace]=A;
K["mouseleave"+this.namespace]=E
}J.Event.bind(this.list,K,this)
};
var B=function(){var K={};
K[(G.browser.opera||G.browser.mozilla?"keypress":"keydown")+this.namespace]=G.proxy(this.__keydownHandler,this);
K["blur"+this.namespace]=G.proxy(this.__blurHandler,this);
K["focus"+this.namespace]=G.proxy(this.__focusHandler,this);
J.Event.bind(this.focusKeeper,K,this)
};
var E=function(K){J.Event.unbind(this.list,"mousemove"+this.namespace);
this.lastMouseX=null;
this.lastMouseY=null
};
var D=function(K){this.lastMouseX=K.pageX;
this.lastMouseY=K.pageY
};
var A=function(K){this.lastMouseX=K.pageX;
this.lastMouseY=K.pageY;
J.Event.bind(this.list,"mousemove"+this.namespace,D,this)
};
var H=function(L){if(this.lastMouseX==null||this.lastMouseX!=L.pageX||this.lastMouseY!=L.pageY){var K=this.__getItem(L);
if(K&&!this.clickRequiredToSelect&&!this.disabled){this.__select(K)
}}};
G.extend(J.ui.List.prototype,(function(){return{name:"list",processItem:function(K){if(this.selectListener.processItem&&typeof this.selectListener.processItem=="function"){this.selectListener.processItem(K)
}},isSelected:function(K){return K.hasClass(this.selectItemCssMarker)
},selectItem:function(K){if(this.selectListener.selectItem&&typeof this.selectListener.selectItem=="function"){this.selectListener.selectItem(K)
}else{K.addClass(this.selectItemCss);
J.Event.fire(this,"selectItem",K)
}this.__scrollToSelectedItem(this)
},unselectItem:function(K){if(this.selectListener.unselectItem&&typeof this.selectListener.unselectItem=="function"){this.selectListener.unselectItem(K)
}else{K.removeClass(this.selectItemCss);
J.Event.fire(this,"unselectItem",K)
}},__focusHandler:function(K){if(!this.focusKeeper.focused){this.focusKeeper.focused=true;
J.Event.fire(this,"listfocus"+this.namespace,K)
}},__blurHandler:function(L){if(!this.isMouseDown){var K=this;
this.timeoutId=window.setTimeout(function(){K.focusKeeper.focused=false;
K.invokeEvent.call(K,"blur",document.getElementById(K.id),L);
J.Event.fire(K,"listblur"+K.namespace,L)
},200)
}else{this.isMouseDown=false
}},__onMouseDown:function(K){this.isMouseDown=true
},__onMouseUp:function(K){this.isMouseDown=false
},__keydownHandler:function(L){if(L.isDefaultPrevented()){return 
}if(L.metaKey){return 
}var K;
if(L.keyCode){K=L.keyCode
}else{if(L.which){K=L.which
}}switch(K){case J.KEYS.DOWN:L.preventDefault();
this.__selectNext();
break;
case J.KEYS.UP:L.preventDefault();
this.__selectPrev();
break;
case J.KEYS.HOME:L.preventDefault();
this.__selectByIndex(0);
break;
case J.KEYS.END:L.preventDefault();
this.__selectByIndex(this.items.length-1);
break;
default:break
}},onClick:function(L){this.setFocus();
var K=this.__getItem(L);
this.processItem(K);
var M=L.metaKey;
if(!this.disabled){this.__select(K,M&&this.clickRequiredToSelect)
}},onDblclick:function(L){this.setFocus();
var K=this.__getItem(L);
this.processItem(K);
if(!this.disabled){this.__select(K,false)
}},currentSelectItem:function(){if(this.items&&this.index!=-1){return G(this.items[this.index])
}},getSelectedItemIndex:function(){return this.index
},removeItems:function(K){G(K).detach();
this.__updateItemsList();
J.Event.fire(this,"removeitems",K)
},removeAllItems:function(){var K=this.__getItems();
this.removeItems(K);
return K
},addItems:function(K){var L=this.scrollContainer;
L.append(K);
this.__updateItemsList();
J.Event.fire(this,"additems",K)
},move:function(K,M){if(M===0){return 
}var L=this;
if(M>0){K=G(K.get().reverse())
}K.each(function(P){var O=L.items.index(this);
var N=O+M;
var Q=L.items[N];
if(M<0){G(this).insertBefore(Q)
}else{G(this).insertAfter(Q)
}L.index=L.index+M;
L.__updateItemsList()
});
J.Event.fire(this,"moveitems",K)
},getItemByIndex:function(K){if(K>=0&&K<this.items.length){return this.items[K]
}},getClientSelectItemByIndex:function(K){if(K>=0&&K<this.items.length){return G(this.items[K]).data("clientSelectItem")
}},resetSelection:function(){var K=this.currentSelectItem();
if(K){this.unselectItem(G(K))
}this.index=-1
},isList:function(K){var L=K.parents("."+this.listCss).attr("id");
return(L&&(L==this.getId()))
},length:function(){return this.items.length
},__updateIndex:function(L){if(L===null){this.index=-1
}else{var K=this.items.index(L);
if(K<0){K=0
}else{if(K>=this.items.length){K=this.items.length-1
}}this.index=K
}},__updateItemsList:function(){return(this.items=this.list.find("."+this.itemCss))
},__storeClientSelectItems:function(K,L){K.each(function(M){var N=G(this);
var P=N.attr("id");
var O=L[P];
N.data("clientSelectItem",O)
})
},__select:function(L,M){var K=this.items.index(L);
this.__selectByIndex(K,M)
},__selectByIndex:function(K,M){if(!this.__isSelectByIndexValid(K)){return 
}if(!this.clickRequiredToSelect&&this.index==K){return 
}var N=this.__unselectPrevious();
if(this.clickRequiredToSelect&&N==K){return 
}this.index=this.__sanitizeSelectedIndex(K);
var L=this.items.eq(this.index);
if(this.isSelected(L)){this.unselectItem(L)
}else{this.selectItem(L)
}},__isSelectByIndexValid:function(K){if(this.items.length==0){return false
}if(K==undefined){this.index=-1;
return false
}return true
},__sanitizeSelectedIndex:function(L){var K;
if(L<0){K=0
}else{if(L>=this.items.length){K=this.items.length-1
}else{K=L
}}return K
},__unselectPrevious:function(){var L=this.index;
if(L!=-1){var K=this.items.eq(L);
this.unselectItem(K);
this.index=-1
}return L
},__selectItemByValue:function(M){var L=null;
this.resetSelection();
var K=this;
this.__getItems().each(function(N){if(G(this).data("clientSelectItem").value==M){K.__selectByIndex(N);
L=G(this);
return false
}});
return L
},csvEncodeValues:function(){var K=new Array();
this.__getItems().each(function(L){K.push(G(this).data("clientSelectItem").value)
});
return K.join(",")
},__selectCurrent:function(){var K;
if(this.items&&this.index>=0){K=this.items.eq(this.index);
this.processItem(K)
}},__getAdjacentIndex:function(L){var K=this.index+L;
if(K<0){K=this.items.length-1
}else{if(K>=this.items.length){K=0
}}return K
},__selectPrev:function(){this.__selectByIndex(this.__getAdjacentIndex(-1))
},__selectNext:function(){this.__selectByIndex(this.__getAdjacentIndex(1))
},__getItem:function(K){return G(K.target).closest("."+this.itemCss,K.currentTarget).get(0)
},__getItems:function(){return this.items
},__setItems:function(K){this.items=K
},__scrollToSelectedItem:function(){if(this.scrollContainer){var L=0;
this.items.slice(0,this.index).each(function(){L+=this.offsetHeight
});
var K=this.scrollContainer;
if(L<K.scrollTop()){K.scrollTop(L)
}else{L+=this.items.get(this.index).offsetHeight;
if(L-K.scrollTop()>K.get(0).clientHeight){K.scrollTop(L-K.innerHeight())
}}}},setFocus:function(){this.focusKeeper.focus()
}}
})())
})(jQuery,window.RichFaces);
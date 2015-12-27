(function(B,I){var A="rf_fu_uid";
var H="rf_fu_uid_alt";
var J="C:\\fakepath\\";
var F='<div class="rf-fu-itm"><span class="rf-fu-itm-lft"><span class="rf-fu-itm-lbl"/><span class="rf-fu-itm-st"/></span><span class="rf-fu-itm-rgh"><a href="javascript:void(0)" class="rf-fu-itm-lnk"/></span></div>';
var E={NEW:"new",UPLOADING:"uploading",DONE:"done",SIZE_EXCEEDED:"sizeExceeded",STOPPED:"stopped",SERVER_ERROR:"serverError"};
var D=function(K){I(this).children(":first").css("background-position","3px 3px").css("padding","4px 4px 2px 22px")
};
var G=function(K){I(this).children(":first").css("background-position","2px 2px").css("padding","3px 5px 3px 21px")
};
B.ui=B.ui||{};
B.ui.FileUpload=B.BaseComponent.extendClass({name:"FileUpload",items:[],submitedItems:[],doneLabel:"Done",sizeExceededLabel:"File size is exceeded",stoppedLabel:"",serverErrorLabel:"Server error",clearLabel:"Clear",deleteLabel:"Delete",init:function(N,L){this.id=N;
I.extend(this,L);
if(this.acceptedTypes){this.acceptedTypes=I.trim(this.acceptedTypes).toUpperCase().split(/\s*,\s*/)
}if(this.maxFilesQuantity){this.maxFilesQuantity=parseInt(I.trim(this.maxFilesQuantity))
}this.element=I(this.attachToDom());
this.form=this.element.parents("form:first");
var M=this.element.children(".rf-fu-hdr:first");
var K=M.children(".rf-fu-btns-lft:first");
this.addButton=K.children(".rf-fu-btn-add:first");
this.uploadButton=this.addButton.next();
this.clearButton=K.next().children(".rf-fu-btn-clr:first");
this.inputContainer=this.addButton.find(".rf-fu-inp-cntr:first");
this.input=this.inputContainer.children("input");
this.list=M.next();
this.hiddenContainer=this.list.next();
this.iframe=this.hiddenContainer.children("iframe:first");
this.progressBarElement=this.iframe.next();
this.progressBar=B.$(this.progressBarElement);
this.cleanInput=this.input.clone();
this.addProxy=I.proxy(this.__addItem,this);
this.input.change(this.addProxy);
this.addButton.mousedown(D).mouseup(G).mouseout(G);
this.uploadButton.click(I.proxy(this.__startUpload,this)).mousedown(D).mouseup(G).mouseout(G);
this.clearButton.click(I.proxy(this.__removeAllItems,this)).mousedown(D).mouseup(G).mouseout(G);
this.iframe.load(I.proxy(this.__load,this));
if(this.onfilesubmit){B.Event.bind(this.element,"onfilesubmit",new Function("event",this.onfilesubmit))
}if(this.ontyperejected){B.Event.bind(this.element,"ontyperejected",new Function("event",this.ontyperejected))
}if(this.onuploadcomplete){B.Event.bind(this.element,"onuploadcomplete",new Function("event",this.onuploadcomplete))
}if(this.onclear){B.Event.bind(this.element,"onclear",new Function("event",this.onclear))
}},__addItem:function(){var L=this.input.val();
if(!navigator.platform.indexOf("Win")){L=L.match(/[^\\]*$/)[0]
}else{if(!L.indexOf(J)){L=L.substr(J.length)
}else{L=L.match(/[^\/]*$/)[0]
}}if(this.__accept(L)&&(!this.noDuplicate||!this.__isFileAlreadyAdded(L))){this.input.hide();
this.input.unbind("change",this.addProxy);
var K=new C(this,L);
this.list.append(K.getJQuery());
this.items.push(K);
this.input=this.cleanInput.clone();
this.inputContainer.append(this.input);
this.input.change(this.addProxy);
this.__updateButtons()
}},__removeItem:function(K){this.items.splice(I.inArray(K,this.items),1);
this.submitedItems.splice(I.inArray(K,this.submitedItems),1);
this.__updateButtons();
B.Event.fire(this.element,"onclear",[K.model])
},__removeAllItems:function(L){var M=[];
for(var K in this.submitedItems){M.push(this.submitedItems[K].model)
}for(var K in this.items){M.push(this.items[K].model)
}this.list.empty();
this.items.splice(0,this.items.length);
this.submitedItems.splice(0,this.submitedItems.length);
this.__updateButtons();
B.Event.fire(this.element,"onclear",M)
},__updateButtons:function(){if(!this.loadableItem&&this.list.children(".rf-fu-itm").size()){if(this.items.length){this.uploadButton.css("display","inline-block")
}else{this.uploadButton.hide()
}this.clearButton.css("display","inline-block")
}else{this.uploadButton.hide();
this.clearButton.hide()
}if(this.maxFilesQuantity&&this.__getTotalItemCount()>=this.maxFilesQuantity){this.addButton.hide()
}else{this.addButton.css("display","inline-block")
}},__startUpload:function(){this.loadableItem=this.items.shift();
this.__updateButtons();
this.loadableItem.startUploading()
},__submit:function(){var N=this.form.attr("action");
var L=this.form.attr("encoding");
var M=this.form.attr("enctype");
try{var K=N.indexOf("?")==-1?"?":"&";
this.form.attr("action",N+K+A+"="+this.loadableItem.uid);
this.form.attr("encoding","multipart/form-data");
this.form.attr("enctype","multipart/form-data");
B.submitForm(this.form,{"org.richfaces.ajax.component":this.id},this.id);
B.Event.fire(this.element,"onfilesubmit",this.loadableItem.model)
}finally{this.form.attr("action",N);
this.form.attr("encoding",L);
this.form.attr("enctype",M);
this.loadableItem.input.removeAttr("name")
}},__load:function(L){if(this.loadableItem){var N=L.target.contentWindow.document;
N=N.XMLDocument||N;
var S=N.documentElement;
var P,M;
if(S.tagName.toUpperCase()=="PARTIAL-RESPONSE"){var R=I(S).children("error");
P=R.length>0?E.SERVER_ERROR:E.DONE
}else{if((M=S.id)&&M.indexOf(A+this.loadableItem.uid+":")==0){P=M.split(":")[1]
}}if(P){var K={source:this.element[0],_mfInternal:{_mfSourceControlId:this.element.attr("id")}};
P==E.DONE&&jsf.ajax.response({responseXML:N},K);
this.loadableItem.finishUploading(P);
this.submitedItems.push(this.loadableItem);
if(P==E.DONE&&this.items.length){this.__startUpload()
}else{this.loadableItem=null;
this.__updateButtons();
var Q=[];
for(var O in this.submitedItems){Q.push(this.submitedItems[O].model)
}for(var O in this.items){Q.push(this.items[O].model)
}B.Event.fire(this.element,"onuploadcomplete",Q)
}}}},__accept:function(N){N=N.toUpperCase();
var K=!this.acceptedTypes;
for(var L=0;
!K&&L<this.acceptedTypes.length;
L++){var M=this.acceptedTypes[L];
K=N.indexOf(M,N.length-M.length)!==-1
}if(!K){B.Event.fire(this.element,"ontyperejected",N)
}return K
},__isFileAlreadyAdded:function(M){var K=false;
for(var L=0;
!K&&L<this.items.length;
L++){K=this.items[L].model.name==M
}K=K||(this.loadableItem&&this.loadableItem.model.name==M);
for(var L=0;
!K&&L<this.submitedItems.length;
L++){K=this.submitedItems[L].model.name==M
}return K
},__getTotalItemCount:function(){return this.__getItemCountByState(this.items,E.NEW)+this.__getItemCountByState(this.submitedItems,E.DONE)
},__getItemCountByState:function(K){var N={};
var M=0;
for(var L=1;
L<arguments.length;
L++){N[arguments[L]]=true
}for(var L=0;
L<K.length;
L++){if(N[K[L].model.state]){M++
}}return M
}});
var C=function(K,L){this.fileUpload=K;
this.input=K.input;
this.model={name:L,state:E.NEW}
};
I.extend(C.prototype,{getJQuery:function(){this.element=I(F);
var K=this.element.children(".rf-fu-itm-lft:first");
this.label=K.children(".rf-fu-itm-lbl:first");
this.state=this.label.nextAll(".rf-fu-itm-st:first");
this.link=K.next().children("a");
this.label.html(this.model.name);
this.link.html(this.fileUpload.deleteLabel);
this.link.click(I.proxy(this.removeOrStop,this));
return this.element
},removeOrStop:function(){this.input.remove();
this.element.remove();
this.fileUpload.__removeItem(this)
},startUploading:function(){this.state.css("display","block");
this.link.html("");
this.input.attr("name",this.fileUpload.id);
this.model.state=E.UPLOADING;
this.uid=Math.random();
this.fileUpload.__submit();
if(this.fileUpload.progressBar){this.fileUpload.progressBar.setValue(0);
this.state.html(this.fileUpload.progressBarElement.detach());
var K={};
K[H]=this.uid;
this.fileUpload.progressBar.enable(K)
}},finishUploading:function(K){if(this.fileUpload.progressBar){this.fileUpload.progressBar.disable();
this.fileUpload.hiddenContainer.append(this.fileUpload.progressBarElement.detach())
}this.input.remove();
this.state.html(this.fileUpload[K+"Label"]);
this.link.html(this.fileUpload.clearLabel);
this.model.state=K
}})
}(window.RichFaces,jQuery));
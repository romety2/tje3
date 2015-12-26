(function ($, rf) {

    rf.ui = rf.ui || {};

    rf.ui.InplaceBase = function(id, options) {
        $super.constructor.call(this, id);
        var mergedOptions = $.extend({}, defaultOptions, options);
        this.editEvent = mergedOptions.editEvent;
        this.noneCss = mergedOptions.noneCss;
        this.changedCss = mergedOptions.changedCss;
        this.editCss = mergedOptions.editCss;
        this.defaultLabel = mergedOptions.defaultLabel;
        this.state = mergedOptions.state;

        this.options = mergedOptions;

        this.element = $(document.getElementById(id));
        this.editContainer = $(document.getElementById(id + "Edit"));
        this.element.bind(this.editEvent, $.proxy(this.__editHandler, this));
        this.isSaved = false;
        this.useDefaultLabel = false;
        this.editState = false;
    };

    rf.ui.InputBase.extend(rf.ui.InplaceBase);
    var $super = rf.ui.InplaceBase.$super;

    var defaultOptions = {
        editEvent: "click",
        state: "ready"
    };

    $.extend(rf.ui.InplaceBase.prototype, ( function () {

        var STATE = {
            READY : 'ready',
            CHANGED: 'changed',
            DISABLE: 'disable',
            EDIT: 'edit'
        };

        return {

            getLabel: function() {
            },

            setLabel: function(value) {
            },

            onshow: function() {
            },

            onhide: function() {
            },

            onsave: function() {
            },

            oncancel: function() {
            },

            save: function() {
                var value = this.__getValue()
                if (value.length > 0) {
                    this.setLabel(value);
                    this.useDefaultLabel = false;
                } else {
                    this.setLabel(this.defaultLabel);
                    this.useDefaultLabel = true;
                }

                this.isSaved = true;

                this.__applyChangedStyles();
                this.onsave();
            },

            cancel: function() {
                var text = "";
                if (!this.useDefaultLabel) {
                    text = this.getLabel();
                }
                this.__setValue(text);
                this.isSaved = true;
                this.oncancel();
            },

            isValueSaved: function() {
                return this.isSaved;
            },

            isEditState: function() {
                return this.editState;
            },

            __applyChangedStyles: function() {
                if (this.isValueChanged()) {
                    this.element.addClass(this.changedCss);
                } else {
                    this.element.removeClass(this.changedCss);
                }
            },

            __show: function() {
                this.scrollElements = rf.Event.bindScrollEventHandlers(this.id, this.__scrollHandler, this);
                this.editState = true;
                this.onshow();
            },

            __hide: function() {
                if (this.scrollElements) {
                    rf.Event.unbindScrollEventHandlers(this.scrollElements, this);
                    this.scrollElements = null;
                }
                this.editState = false;
                this.editContainer.addClass(this.noneCss);
                this.element.removeClass(this.editCss);
                this.onhide();
            },

            __editHandler: function(e) {
                this.isSaved = false;
                this.element.addClass(this.editCss);
                this.editContainer.removeClass(this.noneCss);
                this.__show();
            },
            __scrollHandler: function(e) {
                this.cancel();
            },

            destroy: function () {
                $super.destroy.call(this);
            }
        }

    })());

})(jQuery, window.RichFaces);

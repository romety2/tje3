(function ($, rf) {

    rf.ui = rf.ui || {};

    rf.ui.PickList = function(id, options) {
        var mergedOptions = $.extend({}, defaultOptions, options);
        $super.constructor.call(this, id, mergedOptions);
        this.namespace = this.namespace || "." + rf.Event.createNamespace(this.name, this.id);
        this.attachToDom();
        mergedOptions['scrollContainer'] = $(document.getElementById(id + "SourceItems"));
        this.sourceList = new rf.ui.ListMulti(id+ "SourceList", mergedOptions);
        mergedOptions['scrollContainer'] = $(document.getElementById(id + "TargetItems"));
        this.selectItemCss = mergedOptions['selectItemCss'];
        var hiddenId = id + "SelValue";
        this.hiddenValues = $(document.getElementById(hiddenId));
        mergedOptions['hiddenId'] = hiddenId;
        this.orderable = mergedOptions['orderable'];

        if (this.orderable) {
            this.orderingList = new rf.ui.OrderingList(id+ "Target", mergedOptions);
            this.targetList = this.orderingList.list;
        } else {
            this.targetList = new rf.ui.ListMulti(id+ "TargetList", mergedOptions);
        }
        this.pickList = $(document.getElementById(id));

        this.addButton = $('.rf-pick-add', this.pickList);
        this.addButton.bind("click", $.proxy(this.add, this));
        this.addAllButton = $('.rf-pick-add-all', this.pickList);
        this.addAllButton.bind("click", $.proxy(this.addAll, this));
        this.removeButton = $('.rf-pick-rem', this.pickList);
        this.removeButton.bind("click", $.proxy(this.remove, this));
        this.removeAllButton = $('.rf-pick-rem-all', this.pickList);
        this.removeAllButton.bind("click", $.proxy(this.removeAll, this));
        this.disabled = mergedOptions.disabled;

        if (mergedOptions['onadditems'] && typeof mergedOptions['onadditems'] == 'function') {
            rf.Event.bind(this.targetList, "additems", mergedOptions['onadditems']);
        }
        rf.Event.bind(this.targetList, "additems", $.proxy(this.toggleButtons, this));

        this.focused = false;
        this.keepingFocus = false;
        bindFocusEventHandlers.call(this, mergedOptions);

        // Adding items to the source list happens after removing them from the target list
        if (mergedOptions['onremoveitems'] && typeof mergedOptions['onremoveitems'] == 'function') {
            rf.Event.bind(this.sourceList, "additems", mergedOptions['onremoveitems']);
        }
        rf.Event.bind(this.sourceList, "additems", $.proxy(this.toggleButtons, this));

        rf.Event.bind(this.sourceList, "selectItem", $.proxy(this.toggleButtons, this));
        rf.Event.bind(this.sourceList, "unselectItem", $.proxy(this.toggleButtons, this));
        rf.Event.bind(this.targetList, "selectItem", $.proxy(this.toggleButtons, this));
        rf.Event.bind(this.targetList, "unselectItem", $.proxy(this.toggleButtons, this));

        if (mergedOptions['switchByClick']) {
            rf.Event.bind(this.sourceList, "click", $.proxy(this.add, this));
            rf.Event.bind(this.targetList, "click", $.proxy(this.remove, this));
        }

        if (mergedOptions['switchByDblClick']) {
            rf.Event.bind(this.sourceList, "dblclick", $.proxy(this.add, this));
            rf.Event.bind(this.targetList, "dblclick", $.proxy(this.remove, this));
        }

        if (options['onchange'] && typeof options['onchange'] == 'function') {
            rf.Event.bind(this, "change" + this.namespace, options['onchange']);
        }

        // TODO: Is there a "Richfaces way" of executing a method after page load?
        $(document).ready($.proxy(this.toggleButtons, this));
    };
    rf.BaseComponent.extend(rf.ui.PickList);
    var $super = rf.ui.PickList.$super;

    var defaultOptions = {
        defaultLabel: "",
        itemCss: "rf-pick-opt",
        selectItemCss: "rf-pick-sel",
        listCss: "rf-pick-lst-cord",
        clickRequiredToSelect: true,
        switchByClick : false,
        switchByDblClick : true,
        disabled : false
    };

    var bindFocusEventHandlers = function (options) {
        // source list
        if (options['onsourcefocus'] && typeof options['onsourcefocus'] == 'function') {
            rf.Event.bind(this.sourceList, "listfocus" + this.sourceList.namespace, options['onsourcefocus']);
        }

        if (options['onsourceblur'] && typeof options['onsourceblur'] == 'function') {
            rf.Event.bind(this.sourceList, "listblur" + this.sourceList.namespace, options['onsourceblur']);
        }

        // target list
        if (options['ontargetfocus'] && typeof options['ontargetfocus'] == 'function') {
            rf.Event.bind(this.targetList, "listfocus" + this.targetList.namespace, options['ontargetfocus']);
        }
        if (options['ontargetblur'] && typeof options['ontargetblur'] == 'function') {
            rf.Event.bind(this.targetList, "listblur" + this.targetList.namespace, options['ontargetblur']);
        }

        // pick list
        if (options['onfocus'] && typeof options['onfocus'] == 'function') {
            rf.Event.bind(this, "listfocus" + this.namespace, options['onfocus']);
        }
        if (options['onblur'] && typeof options['onblur'] == 'function') {
            rf.Event.bind(this, "listblur" + this.namespace, options['onblur']);
        }

        this.pickList.focusin($.proxy(this.__focusHandler, this));
        this.pickList.focusout($.proxy(this.__blurHandler, this));
    };

    $.extend(rf.ui.PickList.prototype, (function () {

        return {
            name : "pickList",
            defaultLabelClass : "rf-pick-dflt-lbl",

            getName: function() {
                return this.name;
            },
            getNamespace: function() {
                return this.namespace;
            },

            __focusHandler: function(e) {
                if (! this.focused) {
                    this.focused = true;
                    rf.Event.fire(this, "listfocus" + this.namespace, e);
                    this.originalValue = this.targetList.csvEncodeValues();
                }
            },

            __blurHandler: function(e) {
                if (this.focused) {
                    this.focused = false;
                    rf.Event.fire(this, "listblur" + this.namespace, e);
                    var newValue = this.targetList.csvEncodeValues();
                    if (newValue != this.originalValue) {
                        rf.Event.fire(this, "change" + this.namespace, e);
                    }
                }
            },

            getSourceList: function() {
                return this.sourceList;
            },

            getTargetList: function() {
                return this.targetList;
            },

            add: function() {
                this.targetList.setFocus();
                var items = this.sourceList.removeSelectedItems();
                this.targetList.addItems(items);
                this.encodeHiddenValues();
            },

            remove: function() {
                this.sourceList.setFocus();
                var items = this.targetList.removeSelectedItems();
                this.sourceList.addItems(items);
                this.encodeHiddenValues();
            },

            addAll: function() {
                this.targetList.setFocus();
                var items = this.sourceList.removeAllItems();
                this.targetList.addItems(items);
                this.encodeHiddenValues();
            },

            removeAll: function() {
                this.sourceList.setFocus();
                var items = this.targetList.removeAllItems();
                this.sourceList.addItems(items);
                this.encodeHiddenValues();
            },

            encodeHiddenValues: function() {
                this.hiddenValues.val(this.targetList.csvEncodeValues());
            },

            toggleButtons: function() {
                this.__toggleButton(this.addButton, this.sourceList.__getItems().filter('.' + this.selectItemCss).length > 0);
                this.__toggleButton(this.removeButton, this.targetList.__getItems().filter('.' + this.selectItemCss).length > 0);
                this.__toggleButton(this.addAllButton, this.sourceList.__getItems().length > 0);
                this.__toggleButton(this.removeAllButton, this.targetList.__getItems().length > 0);
                if (this.orderable) {
                    this.orderingList.toggleButtons();
                }
            },

            __toggleButton: function(button, enabled) {
                if (this.disabled || ! enabled) {
                    if (! button.hasClass('rf-pick-btn-dis')) {
                        button.addClass('rf-pick-btn-dis')
                    }
                    if (! button.attr('disabled')) {
                        button.attr('disabled', true);
                    }
                } else {
                    if (button.hasClass('rf-pick-btn-dis')) {
                        button.removeClass('rf-pick-btn-dis')
                    }
                    if (button.attr('disabled')) {
                        button.attr('disabled', false);
                    }
                }
            }
        };
    })());

})(jQuery, window.RichFaces);

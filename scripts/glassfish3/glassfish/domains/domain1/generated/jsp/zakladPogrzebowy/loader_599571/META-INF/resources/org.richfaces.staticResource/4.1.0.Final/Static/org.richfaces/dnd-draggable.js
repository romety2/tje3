/*
 * code review by Pavel Yaschenko
 * 
 * No event's unbindings when component would be destroyed 
 * Hint: easy way to unbind - use namespaces when bind event handlers
 * 
 */

(function ($, rf) {

    rf.ui = rf.ui || {};

    var defaultIndicatorClasses = {
        rejectClass : "rf-ind-rejt",
        acceptClass : "rf-ind-acpt",
        draggingClass : "rf-ind-drag"
    };

    rf.ui.Draggable = function(id, options) {
        this.options = {};
        $.extend(this.options, defaultOptions, options || {});
        $super.constructor.call(this, id);

        this.id = id;

        this.namespace = this.namespace || "."
            + rf.Event.createNamespace(this.name, this.id);

        this.parentId = this.options.parentId;
        this.attachToDom(this.parentId);
        this.dragElement = $(document.getElementById(this.options.parentId));
        this.dragElement.draggable();

        if (options.indicator) {
            var element = document.getElementById(options.indicator);
            this.dragElement.data("indicator", true);
            this.dragElement.draggable("option", "helper", function() {
                return element
            });
        } else {
            this.dragElement.data("indicator", false);
            this.dragElement.draggable("option", "helper", 'clone');
        }

        this.dragElement.draggable("option", "addClasses", false);

        this.dragElement.data('type', this.options.type);
        this.dragElement.data("init", true);
        this.dragElement.data("id", this.id);
        rf.Event.bind(this.dragElement, 'dragstart' + this.namespace, this.dragStart, this);
        rf.Event.bind(this.dragElement, 'drag' + this.namespace, this.drag, this);
        rf.Event.bind(this.dragElement, 'dragstop' + this.namespace, this.dragStop, this);
    };

    rf.BaseNonVisualComponent.extend(rf.ui.Draggable);

    // define super class link
    var $super = rf.ui.Draggable.$super;

    var defaultOptions = {
    };

    $.extend(rf.ui.Draggable.prototype, ( function () {
        return {
            name : "Draggable",
            dragStart: function(e) {
                var ui = e.rf.data;
                var element = ui.helper[0];
                this.parentElement = element.parentNode;
                ui.helper.detach().appendTo("body").setPosition(e).show();

                if (this.__isCustomDragIndicator()) {
                    // move cursor to the center of custom dragIndicator;
                    var left = (ui.helper.width() / 2);
                    var top = (ui.helper.height() / 2);
                    this.dragElement.data('draggable').offset.click.left = left;
                    this.dragElement.data('draggable').offset.click.top = top;
                }
            },

            drag: function(e) {
                var ui = e.rf.data;
                if (this.__isCustomDragIndicator()) {
                    var indicator = rf.$(this.options.indicator);
                    if (indicator) {
                        ui.helper.addClass(indicator.getDraggingClass());
                    } else {
                        ui.helper.addClass(defaultIndicatorClasses.draggingClass);
                    }
                }
                this.__clearDraggableCss(ui.helper);
            },

            dragStop: function(e) {
                var ui = e.rf.data;
                ui.helper.hide().detach().appendTo(this.parentElement);
                if (ui.helper[0] != this.dragElement[0]) {
                    //fix to prevent remove custom indicator from DOM tree. see jQuery draggable._clear method for details
                    ui.helper[0] = this.dragElement[0];
                }
            },

            __isCustomDragIndicator: function() {
                return this.dragElement.data("indicator");
            },

            __clearDraggableCss: function(element) {
                if (element && element.removeClass) {
                    //draggable 'addClasses: false' doesn't work so clear jQuery style
                    element.removeClass("ui-draggable-dragging");
                }
            },

            destroy : function() {
                // clean up code here
                this.detach(this.parentId);
                rf.Event.unbind(this.dragElement, this.namespace);
                // call parent's destroy method
                $super.destroy.call(this);
            }
        }
    })());
})(jQuery, window.RichFaces);

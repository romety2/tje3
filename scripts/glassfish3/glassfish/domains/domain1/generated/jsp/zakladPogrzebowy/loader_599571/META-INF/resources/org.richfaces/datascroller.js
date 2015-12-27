(function ($, richfaces) {

    richfaces.ui = richfaces.ui || {};

    var initButtons = function(buttons, css, component) {
        var id;

        var fn = function(e) {
            e.data.fn.call(e.data.component, e);
        };

        var data = {};
        data.component = component;

        for (id in buttons) {
            var element = $(document.getElementById(id));

            data.id = id;
            data.page = buttons[id];
            data.element = element;
            data.fn = component.processClick;

            element.bind('click', copy(data), fn);
        }
    };

    var copy = function(data) {
        var key;
        var eventData = {};

        for (key in data) {
            eventData[key] = data[key];
        }

        return eventData;
    };

    var togglePressClass = function(el, event) {
        if (event.type == 'mousedown') {
            el.addClass('rf-ds-press');
        } else if (event.type == 'mouseup' || event.type == 'mouseout') {
            el.removeClass('rf-ds-press');
        }
    };

    richfaces.ui.DataScroller = function(id, submit, options) {

        $super.constructor.call(this, id);

        var dataScrollerElement = this.attachToDom();

        this.options = options;
        this.currentPage = options.currentPage;

        if (submit && typeof submit == 'function') {
            RichFaces.Event.bindById(id, this.getScrollEventName(), submit);
        }

        var css = {};

        if (options.buttons) {

            $(dataScrollerElement).delegate('.rf-ds-btn', 'mouseup mousedown mouseout', function(event) {
                if ($(this).hasClass('rf-ds-dis')) {
                    $(this).removeClass('rf-ds-press');
                } else {
                    togglePressClass($(this), event);
                }
            });

            initButtons(options.buttons.left, css, this);
            initButtons(options.buttons.right, css, this);
        }

        if (options.digitals) {

            $(dataScrollerElement).delegate('.rf-ds-nmb-btn', 'mouseup mousedown mouseout', function(event) {
                togglePressClass($(this), event);
            });

            initButtons(options.digitals, css, this);
        }
    };

    richfaces.BaseComponent.extend(richfaces.ui.DataScroller);
    var $super = richfaces.ui.DataScroller.$super;

    $.extend(richfaces.ui.DataScroller.prototype, (function () {

        var scrollEventName = "rich:datascroller:onscroll";

        return {

            name: "RichFaces.ui.DataScroller",

            processClick: function(event) {
                var data = event.data;
                if (data) {
                    var page = data.page;
                    if (page) {
                        this.switchToPage(page);
                    }
                }
            },

            switchToPage: function(page) {
                if (typeof page != 'undefined' && page != null) {
                    RichFaces.Event.fireById(this.id, this.getScrollEventName(), {'page' : page});
                }
            },

            fastForward: function() {
                this.switchToPage("fastforward");
            },

            fastRewind: function() {
                this.switchToPage("fastrewind");
            },

            next: function() {
                this.switchToPage("next");
            },

            previous: function() {
                this.switchToPage("previous");
            },

            first: function() {
                this.switchToPage("first");
            },

            last: function() {
                this.switchToPage("last");
            },

            getScrollEventName: function() {
                return scrollEventName;
            },
            destroy: function() {
                $super.destroy.call(this);
            }
        }

    })());

})(jQuery, window.RichFaces);
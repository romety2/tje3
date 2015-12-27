(function($, rf) {

    // Constructor definition
    rf.ui.NotifyMessage = function(componentId, options, notifyOptions) {
        // call constructor of parent class
        $super.constructor.call(this, componentId, options, defaultOptions);
        this.notifyOptions = notifyOptions;
    };

    // Extend component class and add protected methods from parent class to our container
    rf.ui.Base.extend(rf.ui.NotifyMessage);

    // define super class link
    var $super = rf.ui.NotifyMessage.$super;

    var defaultOptions = {
        showSummary:true,
        level:0,
        isMessages: false
    };


    var onMessage = function (event, element, data) {
        var sourceId = data.sourceId;
        var message = data.message;
        if (!this.options.forComponentId) {
            if (message) {
                renderMessage.call(this, sourceId, message);
            }
        } else if (this.options.forComponentId === sourceId) {
            renderMessage.call(this, sourceId, message);
        }
    }

    var renderMessage = function(index, message) {
        if (message && message.severity >= this.options.level) {
            showNotification.call(this, message);
        }
    }
    
    var showNotification = function(message) {
        RichFaces.ui.Notify($.extend({}, this.notifyOptions, {
            'summary': this.options.showSummary ? message.summary : undefined,
            'detail': this.options.showDetail ? message.detail : undefined,
            'severity': message.severity
        }));
    }

    var bindEventHandlers = function () {
        rf.Event.bind(window.document, rf.Event.MESSAGE_EVENT_TYPE + this.namespace, onMessage, this);
    };

    $.extend(rf.ui.NotifyMessage.prototype, {
            name: "NotifyMessage",
            __bindEventHandlers: bindEventHandlers,
            
            destroy : function() {
                rf.Event.unbind(window.document, rf.Event.MESSAGE_EVENT_TYPE + this.namespace);
                $super.destroy.call(this);
            }
        });

})(jQuery, window.RichFaces || (window.RichFaces = {}));
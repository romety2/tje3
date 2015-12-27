(function($, rf) {
    
    rf.ui = rf.ui || {};
    
    var defaultOptions = {
        position: "topRight",
        direction: "vertical",
        method: "last",
        notifications: [],
        addNotification: function(pnotify) {
            this.notifications.push(pnotify);
        }
    };

    rf.ui.NotifyStack = rf.BaseComponent.extendClass({
        
        name : "NotifyStack",

        init : function(componentId, options) {
            $super.constructor.call(this, componentId);
            this.attachToDom(this.id);
            this.__initializeStack(options);
        },
        
        __initializeStack : function(options) {
            var stack = $.extend({}, $.pnotify.defaults.pnotify_stack, defaultOptions, options);
            
            var isVertical = (stack.direction == 'vertical');
            var isFirst = (stack.method == 'first');
            
            stack.push = isFirst ? 'top' : 'bottom';
            
            switch (stack.position) {
                case "topLeft":
                    stack.dir1 = isVertical ? 'down' : 'right';
                    stack.dir2 = isVertical ? 'right' : 'down';
                    break;
                case "topRight":
                    stack.dir1 = isVertical ? 'down' : 'left';
                    stack.dir2 = isVertical ? 'left' : 'down';
                    break;
                case "bottomLeft":
                    stack.dir1 = isVertical ? 'up' : 'right';
                    stack.dir2 = isVertical ? 'right' : 'up';
                    break;
                case "bottomRight":
                    stack.dir1 = isVertical ? 'up' : 'left';
                    stack.dir2 = isVertical ? 'left' : 'up';
                    break;
                default:
                    throw "wrong stack position: " + stack.position;
            }
            
            this.stack = stack;
        },
    
        getStack : function() {
            return this.stack;
        },
        
        removeNotifications: function() {
            var pnotify;
            while (pnotify = this.stack.notifications.pop()) {
                pnotify.pnotify_remove();
            }
        },
        
        destroy : function() {
            this.removeNotifications();
            this.stack = null;
            $super.destroy.call(this);
        }
    });
    
    var $super = rf.ui.NotifyStack.$super;

})(jQuery, RichFaces);
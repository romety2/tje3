(function ($, rf) {

    rf.ui = rf.ui || {};

    // Constructor definition
    rf.ui.AutocompleteBase = function(componentId, selectId, fieldId, options) {
        // call constructor of parent class
        $super.constructor.call(this, componentId);
        this.selectId = selectId;
        this.fieldId = fieldId;
        this.options = $.extend({}, defaultOptions, options);
        this.namespace = this.namespace || "." + rf.Event.createNamespace(this.name, this.selectId);
        this.currentValue = "";
        this.tempValue = this.getValue();
        this.isChanged = this.tempValue.length != 0;
        bindEventHandlers.call(this);
    };

    // Extend component class and add protected methods from parent class to our container
    rf.BaseComponent.extend(rf.ui.AutocompleteBase);

    // define super class link
    var $super = rf.ui.AutocompleteBase.$super;

    var defaultOptions = {
        changeDelay:8
    };

    var bindEventHandlers = function() {

        var inputEventHandlers = {};

        if (this.options.buttonId) {
            inputEventHandlers["mousedown" + this.namespace] = onButtonShow;
            inputEventHandlers["mouseup" + this.namespace] = onSelectMouseUp;
            rf.Event.bindById(this.options.buttonId, inputEventHandlers, this);
        }

        inputEventHandlers = {};
        inputEventHandlers["focus" + this.namespace] = onFocus;
        inputEventHandlers["blur" + this.namespace] = onBlur;
        inputEventHandlers["click" + this.namespace] = onClick;
        inputEventHandlers[($.browser.opera || $.browser.mozilla ? "keypress" : "keydown") + this.namespace] = onKeyDown;
        inputEventHandlers["change" + this.namespace] = function (event) {
            if (this.focused) {
                event.stopPropagation()
            }
        };
        rf.Event.bindById(this.fieldId, inputEventHandlers, this);

        inputEventHandlers = {};
        inputEventHandlers["mousedown" + this.namespace] = onSelectMouseDown;
        inputEventHandlers["mouseup" + this.namespace] = onSelectMouseUp;
        rf.Event.bindById(this.selectId, inputEventHandlers, this);
    };

    var onSelectMouseDown = function () {
        this.isMouseDown = true;
    };
    var onSelectMouseUp = function () {
        rf.getDomElement(this.fieldId).focus();
    };

    var onButtonShow = function (event) {
        this.isMouseDown = true;
        if (this.timeoutId) {
            window.clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }

        rf.getDomElement(this.fieldId).focus();
        if (this.isVisible) {
            this.__hide(event);
        } else {
            onShow.call(this, event);
        }
    };

    var onFocus = function (event) {
        if (!this.focused) {
            this.__focusValue = this.getValue();
            this.focused = true;
            this.invokeEvent("focus", rf.getDomElement(this.fieldId), event);
        }
    };

    var onBlur = function (event) {
        if (this.isMouseDown) {
            rf.getDomElement(this.fieldId).focus();
            this.isMouseDown = false;
        } else if (!this.isMouseDown) {
            if (this.isVisible) {
                var _this = this;
                this.timeoutId = window.setTimeout(function() {
                    _this.__hide(event);
                }, 200);
            }
            if (this.focused) {
                this.focused = false;
                this.invokeEvent("blur", rf.getDomElement(this.fieldId), event);
                if (this.__focusValue != this.getValue()) {
                    this.invokeEvent("change", rf.getDomElement(this.fieldId), event);
                    this.invokeEvent("change", rf.getDomElement(this.id), event);
                }
            }
        }
    };

    var onClick = function (event) {
    };

    var onChange = function (event) {
        if (this.isChanged) {
            if (this.getValue() == this.tempValue) return;
        }
        this.isChanged = false;
        var value = this.getValue();
        var flag = value != this.currentValue;
        //TODO: is it needed to chesk keys?
        //TODO: we need to set value when autoFill used when LEFT or RIGHT was pressed
        if (event.keyCode == rf.KEYS.LEFT || event.keyCode == rf.KEYS.RIGHT || flag) {
            if (flag) {
                this.currentValue = this.getValue();
                this.__onChangeValue(event, undefined, (!this.isVisible ? this.__show : undefined));
            } else if (this.isVisible) {
                this.__onChangeValue(event);
            }
        }
    };

    var onShow = function (event) {
        if (this.isChanged) {
            this.isChanged = false;
            onChange.call(this, {});
        } else {
            !this.__updateState(event) && this.__show(event);
        }
    };

    var onKeyDown = function (event) {
        switch (event.keyCode) {
            case rf.KEYS.UP:
                event.preventDefault();
                if (this.isVisible) {
                    this.__onKeyUp(event);
                }
                break;
            case rf.KEYS.DOWN:
                event.preventDefault();
                if (this.isVisible) {
                    this.__onKeyDown(event);
                } else {
                    onShow.call(this, event);
                }
                break;
            case rf.KEYS.PAGEUP:
                if (this.isVisible) {
                    event.preventDefault();
                    this.__onPageUp(event);
                }
                break;
            case rf.KEYS.PAGEDOWN:
                if (this.isVisible) {
                    event.preventDefault();
                    this.__onPageDown(event);
                }
                break;
            case rf.KEYS.HOME:
                if (this.isVisible) {
                    event.preventDefault();
                    this.__onKeyHome(event);
                }
                break;
            case rf.KEYS.END:
                if (this.isVisible) {
                    event.preventDefault();
                    this.__onKeyEnd(event);
                }
                break;
            case rf.KEYS.RETURN:
                if (this.isVisible) {
                    event.preventDefault();
                    this.__onEnter(event);
                    //TODO: bind form submit event handler to cancel form submit under the opera
                    //cancelSubmit = true;
                    this.__hide(event);
                    return false;
                }
                break;
            case rf.KEYS.ESC:
                this.__hide(event);
                break;
            default:
                if (!this.options.selectOnly) {
                    var _this = this;
                    window.clearTimeout(this.changeTimerId);
                    this.changeTimerId = window.setTimeout(function() {
                        onChange.call(_this, event);
                    }, this.options.changeDelay)
                }
                break;
        }
    };

    /*
     * public API functions definition
     */
    var show = function (event) {
        if (!this.isVisible) {
            if (this.__onBeforeShow(event) != false) {
                this.scrollElements = rf.Event.bindScrollEventHandlers(this.selectId, this.__hide, this, this.namespace);
                var element = rf.getDomElement(this.selectId);
                if (this.options.attachToBody) {
                    this.parentElement = element.parentNode;
                    document.body.appendChild(element);
                }
                $(element).setPosition({id: this.fieldId}, {type:"DROPDOWN"}).show();
                this.isVisible = true;
                this.__onShow(event);
            }
        }
    };
    var hide = function (event) {
        if (this.isVisible) {
            rf.Event.unbindScrollEventHandlers(this.scrollElements, this);
            this.scrollElements = null;
            $(rf.getDomElement(this.selectId)).hide();
            this.isVisible = false;
            if (this.options.attachToBody && this.parentElement) {
                this.parentElement.appendChild(rf.getDomElement(this.selectId));
                this.parentElement = null;
            }
            this.__onHide(event);
        }
    };

    var updateInputValue = function (value) {
        if (this.fieldId) {
            rf.getDomElement(this.fieldId).value = value;
            return value;
        } else {
            return "";
        }
    };

    /*
     * Prototype definition
     */
    $.extend(rf.ui.AutocompleteBase.prototype, (function () {
        return {
            /*
             * public API functions
             */
            name:"AutocompleteBase",
            showPopup: function (event) {
                if (!this.focused) {
                    rf.getDomElement(this.fieldId).focus();
                }
                onShow.call(this, event);
            },
            hidePopup: function (event) {
                this.__hide(event)
            },
            getNamespace: function () {
                return this.namespace;
            },
            getValue: function () {
                return this.fieldId ? rf.getDomElement(this.fieldId).value : "";
            },
            setValue: function (value) {
                if (value == this.currentValue) return;
                updateInputValue.call(this, value);
                this.isChanged = true;
            },
            /*
             * Protected methods
             */
            __updateInputValue: updateInputValue,
            __show: show,
            __hide: hide,
            /*
             * abstract protected methods
             */
            __onChangeValue: function (event) {
            },
            __onKeyUp: function (event) {
            },
            __onKeyDown: function (event) {
            },
            __onPageUp: function (event) {
            },
            __onPageDown: function (event) {
            },
            __onKeyHome: function (event) {
            },
            __onKeyEnd: function (event) {
            },
            __onBeforeShow: function (event) {
            },
            __onShow: function (event) {
            },
            __onHide: function (event) {
            },
            /*
             * Destructor
             */
            destroy: function () {
                this.parentNode = null;
                if (this.scrollElements) {
                    rf.Event.unbindScrollEventHandlers(this.scrollElements, this);
                    this.scrollElements = null;
                }
                this.options.buttonId && rf.Event.unbindById(this.options.buttonId, this.namespace);
                rf.Event.unbindById(this.fieldId, this.namespace);
                rf.Event.unbindById(this.selectId, this.namespace);
                $super.destroy.call(this);
            }
        };
    })());
})(jQuery, RichFaces);
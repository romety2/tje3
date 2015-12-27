/*
 * JBoss, Home of Professional Open Source
 * Copyright ${year}, Red Hat, Inc. and individual contributors
 * by the @authors tag. See the copyright.txt in the distribution for a
 * full listing of individual contributors.
 *
 * This is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation; either version 2.1 of
 * the License, or (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this software; if not, write to the Free
 * Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301 USA, or see the FSF site: http://www.fsf.org.
 */
(function(richfaces, jQuery) {
    richfaces.ui = richfaces.ui || {};

    richfaces.ui.InputNumberSlider = richfaces.BaseComponent.extendClass({

            name: "InputNumberSlider",

            delay: 200,
            maxValue: 100,
            minValue: 0,
            step: 1,
            tabIndex: 0,

            decreaseSelectedClass: "rf-insl-dec-sel",
            handleSelectedClass: "rf-insl-hnd-sel",
            increaseSelectedClass: "rf-insl-inc-sel",

            init: function (id, options, selectedClasses) {
                $superInputNumberSlider.constructor.call(this, id);
                jQuery.extend(this, options);
                this.range = this.maxValue - this.minValue;
                this.id = id;
                this.element = jQuery(this.attachToDom());
                this.input = this.element.children(".rf-insl-inp-cntr").children(".rf-insl-inp");
                this.track = this.element.children(".rf-insl-trc-cntr").children(".rf-insl-trc");
                this.handleContainer = this.track.children("span");
                this.handle = this.handleContainer.children(".rf-insl-hnd, .rf-insl-hnd-dis");
                this.tooltip = this.element.children(".rf-insl-tt");

                var value = Number(this.input.val());
                if (isNaN(value)) {
                    value = this.minValue;
                }
                this.handleContainer.css("display", "block");
                this.track.css("padding-right", this.handle.width() + "px");
                this.__setValue(value, null, true);

                if (!this.disabled) {
                    this.decreaseButton = this.element.children(".rf-insl-dec");
                    this.increaseButton = this.element.children(".rf-insl-inc");

                    this.track[0].tabIndex = this.tabIndex;

                    for (var i in selectedClasses) {
                        this[i] += " " + selectedClasses[i];
                    }
                    var proxy = jQuery.proxy(this.__inputHandler, this);
                    this.input.change(proxy);
                    this.input.submit(proxy);
                    this.element.mousewheel(jQuery.proxy(this.__mousewheelHandler, this));
                    this.track.keydown(jQuery.proxy(this.__keydownHandler, this));
                    this.decreaseButton.mousedown(jQuery.proxy(this.__decreaseHandler, this));
                    this.increaseButton.mousedown(jQuery.proxy(this.__increaseHandler, this));
                    this.track.mousedown(jQuery.proxy(this.__mousedownHandler, this));
                }
            },

            decrease: function (event) {
                var value = this.value - this.step;
                value = this.roundFloat(value);
                this.setValue(value, event);
            },

            increase: function (event) {
                var value = this.value + this.step;
                value = this.roundFloat(value);
                this.setValue(value, event);
            },

            getValue: function () {
                return this.value;
            },

            setValue: function (value, event) {
                if (!this.disabled) {
                    this.__setValue(value, event);
                }
            },

            roundFloat: function(x){
                var str = this.step.toString();
                var power = 0;
                if (!/\./.test(str)) {
                    if (this.step >= 1) {
                        return x;
                    }
                    if (/e/.test(str)) {
                        power = str.split("-")[1];
                    }
                } else {
                    power = str.length - str.indexOf(".") - 1;
                }
                var ret = x.toFixed(power);
                return parseFloat(ret);
            },

            __setValue: function (value, event, skipOnchange) {
                if (!isNaN(value)) {
                    if (value > this.maxValue) {
                        value = this.maxValue;
                    } else if (value < this.minValue) {
                        value = this.minValue;
                    }
                    if (value != this.value) {
                        this.input.val(value);
                        var left = 100 * (value - this.minValue) / this.range;
                        this.handleContainer.css("padding-left", left + "%");
                        this.tooltip.text(value);
                        this.tooltip.setPosition(this.handle, {from: 'LT', offset: [0, 5]}); //TODO Seems offset doesn't work now.
                        this.value = value;
                        if (this.onchange && !skipOnchange) {
                            this.onchange.call(this.element[0], event);
                        }
                    }
                }
            },

            __inputHandler: function (event) {
                var value = Number(this.input.val());
                if (isNaN(value)) {
                    this.input.val(this.value);
                } else {
                    this.__setValue(value, event);
                }
            },

            __mousewheelHandler: function (event, delta, deltaX, deltaY) {
                delta = deltaX || deltaY;
                if (delta > 0) {
                    this.increase(event);
                } else if (delta < 0) {
                    this.decrease(event);
                }
                return false;
            },

            __keydownHandler: function (event) {
                if (event.keyCode == 37) { //LEFT
                    var value = Number(this.input.val()) - this.step;
                    value = this.roundFloat(value);
                    this.__setValue(value, event);
                    event.preventDefault();
                } else if (event.keyCode == 39) { //RIGHT
                    var value = Number(this.input.val()) + this.step;
                    value = this.roundFloat(value);
                    this.__setValue(value, event);
                    event.preventDefault();
                }
            },

            __decreaseHandler: function (event) {
                var component = this;
                component.decrease(event);
                this.intervalId = window.setInterval(function() {
                    component.decrease(event);
                }, this.delay);
                jQuery(document).one("mouseup", true, jQuery.proxy(this.__clearInterval, this));
                this.decreaseButton.addClass(this.decreaseSelectedClass);
                event.preventDefault();
            },

            __increaseHandler: function (event) {
                var component = this;
                component.increase(event);
                this.intervalId = window.setInterval(function() {
                    component.increase(event);
                }, this.delay);
                jQuery(document).one("mouseup", jQuery.proxy(this.__clearInterval, this));
                this.increaseButton.addClass(this.increaseSelectedClass);
                event.preventDefault();
            },

            __clearInterval: function (event) {
                window.clearInterval(this.intervalId);
                if (event.data) { // decreaseButton
                    this.decreaseButton.removeClass(this.decreaseSelectedClass);
                } else {
                    this.increaseButton.removeClass(this.increaseSelectedClass);
                }
            },

            __mousedownHandler: function (event) {
                this.__mousemoveHandler(event);
                this.track.focus();
                var jQueryDocument = jQuery(document);
                jQueryDocument.mousemove(jQuery.proxy(this.__mousemoveHandler, this));
                jQueryDocument.one("mouseup", jQuery.proxy(this.__mouseupHandler, this));
                this.handle.addClass(this.handleSelectedClass);
                this.tooltip.show();
            },

            __mousemoveHandler: function (event) {
                var value = this.range * (event.pageX - this.track.position().left - this.handle.width() / 2) / (this.track.width()
                    - this.handle.width()) + this.minValue;
                value = Math.round(value / this.step) * this.step;
                value = this.roundFloat(value);
                this.__setValue(value, event);
                event.preventDefault();
            },

            __mouseupHandler: function () {
                this.handle.removeClass(this.handleSelectedClass);
                this.tooltip.hide();
                jQuery(document).unbind("mousemove", this.__mousemoveHandler);
            },

            destroy: function (event) {
                jQuery(document).unbind("mousemove", this.__mousemoveHandler);
                $superInputNumberSlider.destroy.call(this);
            }
        });
    $superInputNumberSlider = richfaces.ui.InputNumberSlider.$super;
}(window.RichFaces, jQuery));
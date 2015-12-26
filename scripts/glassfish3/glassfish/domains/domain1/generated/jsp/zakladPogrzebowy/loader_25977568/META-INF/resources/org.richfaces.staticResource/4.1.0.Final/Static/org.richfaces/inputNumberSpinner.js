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

    richfaces.ui.InputNumberSpinner = richfaces.BaseComponent.extendClass({

            name: "InputNumberSpinner",

            cycled: true,
            delay: 200,
            maxValue: 100,
            minValue: 0,
            step: 1,

            init: function (id, options) {
                $super.constructor.call(this, id);
                jQuery.extend(this, options);
                this.element = jQuery(this.attachToDom());
                this.input = this.element.children(".rf-insp-inp");

                var value = Number(this.input.val());
                if (isNaN(value)) {
                    value = this.minValue;
                }
                this.__setValue(value, null, true);

                if (!this.input.attr("disabled")) {
                    var buttonsArea = this.element.children(".rf-insp-btns");
                    this.decreaseButton = buttonsArea.children(".rf-insp-dec");
                    this.increaseButton = buttonsArea.children(".rf-insp-inc");

                    var proxy = jQuery.proxy(this.__inputHandler, this)
                    this.input.change(proxy);
                    this.input.submit(proxy);
                    this.input.submit(proxy);
                    this.input.mousewheel(jQuery.proxy(this.__mousewheelHandler, this));
                    this.input.keydown(jQuery.proxy(this.__keydownHandler, this));
                    this.decreaseButton.mousedown(jQuery.proxy(this.__decreaseHandler, this));
                    this.increaseButton.mousedown(jQuery.proxy(this.__increaseHandler, this));
                }
            },

            decrease: function (event) {
                var value = this.value - this.step;
                value = this.roundFloat(value);
                if (value < this.minValue && this.cycled) {
                    value = this.maxValue;
                }
                this.__setValue(value, event);
            },

            increase: function (event) {
                var value = this.value + this.step;
                value = this.roundFloat(value);

                if (value > this.maxValue && this.cycled) {
                    value = this.minValue;
                }
                this.__setValue(value, event);
            },

            getValue: function () {
                return this.value;
            },

            setValue: function (value, event) {
                if (!this.input.attr("disabled")) {
                    this.__setValue(value);
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

            destroy: function (event) {
                if (this.intervalId) {
                    window.clearInterval(this.intervalId);
                    this.decreaseButton.css("backgroundPosition", " 50% 40%").unbind("mouseout", this.destroy)
                        .unbind("mouseup", this.destroy);
                    this.increaseButton.css("backgroundPosition", " 50% 40%").unbind("mouseout", this.destroy)
                        .unbind("mouseup", this.destroy);
                    this.intervalId = null;
                }
                $super.destroy.call(this);
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
                if (event.keyCode == 40) { //DOWN
                    this.decrease(event);
                    event.preventDefault();
                } else if (event.keyCode == 38) { //UP
                    this.increase(event);
                    event.preventDefault();
                }
            },

            __decreaseHandler: function (event) {
                var component = this;
                component.decrease(event);
                this.intervalId = window.setInterval(function() {
                    component.decrease(event);
                }, this.delay);
                var proxy = jQuery.proxy(this.destroy, this);
                this.decreaseButton.bind("mouseup", proxy).bind("mouseout", proxy)
                    .css("backgroundPosition", "60% 60%");
                event.preventDefault();
            },

            __increaseHandler: function (event) {
                var component = this;
                component.increase(event);
                this.intervalId = window.setInterval(function() {
                    component.increase(event);
                }, this.delay);
                var proxy = jQuery.proxy(this.destroy, this);
                this.increaseButton.bind("mouseup", proxy).bind("mouseout", proxy)
                    .css("backgroundPosition", "60% 60%");
                event.preventDefault();
            }
        });

    // define super class link
    var $super = richfaces.ui.InputNumberSpinner.$super;
}(window.RichFaces, jQuery));
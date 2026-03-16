odoo.define('df_patient_odontogram.odontogram_field', function (require) {
    "use strict";

    const AbstractField = require('web.AbstractField');
    const fieldRegistry = require('web.field_registry');
    const core = require('web.core');

    const QWeb = core.qweb;
    const _t = core._t;

    const PERMANENT_UPPER_LEFT = ["18", "17", "16", "15", "14", "13", "12", "11"];
    const PERMANENT_UPPER_RIGHT = ["21", "22", "23", "24", "25", "26", "27", "28"];
    const PERMANENT_LOWER_LEFT = ["48", "47", "46", "45", "44", "43", "42", "41"];
    const PERMANENT_LOWER_RIGHT = ["31", "32", "33", "34", "35", "36", "37", "38"];

    const PRIMARY_UPPER_LEFT = ["55", "54", "53", "52", "51"];
    const PRIMARY_UPPER_RIGHT = ["61", "62", "63", "64", "65"];
    const PRIMARY_LOWER_LEFT = ["85", "84", "83", "82", "81"];
    const PRIMARY_LOWER_RIGHT = ["71", "72", "73", "74", "75"];

    const EMPTY_TOOTH = () => ({
        status: "healthy",
        mobility: "",
        recession: "",
        notes: "",
    });

    const OdontogramField = AbstractField.extend({
        supportedFieldTypes: ['text'],
        className: 'o_df_odontogram_field',
        events: {
            'click .o_df_tooth': '_onToothClick',
            'click .o_df_status_btn': '_onStatusClick',
            'input .o_df_tooth_input': '_onInputChange',
        },

        init: function () {
            this._super.apply(this, arguments);
            this.currentToothCode = null;
            this.payload = this._parseValue(this.value);
        },

        _parseValue: function (value) {
            let payload = { teeth: {} };
            try {
                payload = JSON.parse(value || '{"teeth":{}}');
            } catch (err) {
                payload = { teeth: {} };
            }
            payload.teeth = payload.teeth || {};
            const allCodes = [].concat(
                PERMANENT_UPPER_LEFT,
                PERMANENT_UPPER_RIGHT,
                PERMANENT_LOWER_LEFT,
                PERMANENT_LOWER_RIGHT,
                PRIMARY_UPPER_LEFT,
                PRIMARY_UPPER_RIGHT,
                PRIMARY_LOWER_LEFT,
                PRIMARY_LOWER_RIGHT
            );
            allCodes.forEach((code) => {
                payload.teeth[code] = Object.assign(EMPTY_TOOTH(), payload.teeth[code] || {});
            });
            return payload;
        },

        _getValue: function () {
            return JSON.stringify(this.payload);
        },

        _render: function () {
            this.payload = this._parseValue(this.value);
            if (!this.currentToothCode) {
                this.currentToothCode = '11';
            }
            this.$el.html(QWeb.render('df_patient_odontogram.OdontogramField', {
                widget: this,
                payload: this.payload,
            }));
            this._refreshInspector();
        },

        _getPermanentUpper: function () {
            return [PERMANENT_UPPER_LEFT, PERMANENT_UPPER_RIGHT];
        },

        _getPermanentLower: function () {
            return [PERMANENT_LOWER_LEFT, PERMANENT_LOWER_RIGHT];
        },

        _getPrimaryUpper: function () {
            return [PRIMARY_UPPER_LEFT, PRIMARY_UPPER_RIGHT];
        },

        _getPrimaryLower: function () {
            return [PRIMARY_LOWER_LEFT, PRIMARY_LOWER_RIGHT];
        },

        _getToothClass: function (code) {
            const item = this.payload.teeth[code] || EMPTY_TOOTH();
            const classes = ['o_df_tooth'];
            classes.push('o_df_status_' + (item.status || 'healthy'));
            if (this.currentToothCode === code) {
                classes.push('o_df_selected');
            }
            return classes.join(' ');
        },

        _getToothState: function (code) {
            return this.payload.teeth[code] || EMPTY_TOOTH();
        },

        _onToothClick: function (ev) {
            ev.preventDefault();
            const code = ev.currentTarget.dataset.code;
            this.currentToothCode = code;
            this._render();
        },

        _onStatusClick: function (ev) {
            ev.preventDefault();
            const status = ev.currentTarget.dataset.status;
            const item = this.payload.teeth[this.currentToothCode] || EMPTY_TOOTH();
            item.status = status;
            this.payload.teeth[this.currentToothCode] = item;
            this._saveAndRender();
        },

        _onInputChange: function () {
            const item = this.payload.teeth[this.currentToothCode] || EMPTY_TOOTH();
            item.mobility = this.$('.o_df_input_mobility').val() || '';
            item.recession = this.$('.o_df_input_recession').val() || '';
            item.notes = this.$('.o_df_input_notes').val() || '';
            this.payload.teeth[this.currentToothCode] = item;
            this._saveAndRender(false);
        },

        _saveAndRender: function (rerender = true) {
            this._setValue(this._getValue());
            if (rerender) {
                this._render();
            } else {
                this._refreshInspector();
                this._highlightSelection();
            }
        },

        _highlightSelection: function () {
            this.$('.o_df_tooth').removeClass('o_df_selected');
            this.$('.o_df_tooth[data-code="' + this.currentToothCode + '"]').addClass('o_df_selected');
        },

        _refreshInspector: function () {
            const item = this.payload.teeth[this.currentToothCode] || EMPTY_TOOTH();
            this.$('.o_df_current_tooth').text(this.currentToothCode || '-');
            this.$('.o_df_input_mobility').val(item.mobility || '');
            this.$('.o_df_input_recession').val(item.recession || '');
            this.$('.o_df_input_notes').val(item.notes || '');
            this.$('.o_df_status_btn').removeClass('active');
            this.$('.o_df_status_btn[data-status="' + (item.status || 'healthy') + '"]').addClass('active');
        },
    });

    fieldRegistry.add('df_odontogram', OdontogramField);

    return OdontogramField;
});

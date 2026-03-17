/** @odoo-module **/

import { Component, useState, useRef } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { registry } from "@web/core/registry";

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

function parsePayload(value) {
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
}

export class OdontogramField extends Component {
    static template = "df_patient_odontogram.OdontogramField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        // Refs OWL (no this.refs): permiten acceder a inputs y al contenedor del panel
        this.inspectorWrapperRef = useRef("inspectorWrapperRef");
        this.mobilityRef = useRef("mobilityRef");
        this.recessionRef = useRef("recessionRef");
        this.notesRef = useRef("notesRef");

        this.state = useState({
            payload: parsePayload(this.props.value),
            currentToothCode: "11",
            panelPosition: null, // null = en columna lateral; { left, top } = posición flotante arrastrable
            dragStart: null,
        });
        this._boundDragMove = this._onPanelDragMove.bind(this);
        this._boundDragEnd = this._onPanelDragEnd.bind(this);
    }

    onWillUpdateProps(nextProps) {
        if (nextProps.value !== this.props.value) {
            this.state.payload = parsePayload(nextProps.value);
        }
    }

    get payload() {
        return this.state.payload;
    }

    get currentToothCode() {
        return this.state.currentToothCode;
    }

    getPermanentUpper() {
        return [PERMANENT_UPPER_LEFT, PERMANENT_UPPER_RIGHT];
    }

    getPermanentLower() {
        return [PERMANENT_LOWER_LEFT, PERMANENT_LOWER_RIGHT];
    }

    getPrimaryUpper() {
        return [PRIMARY_UPPER_LEFT, PRIMARY_UPPER_RIGHT];
    }

    getPrimaryLower() {
        return [PRIMARY_LOWER_LEFT, PRIMARY_LOWER_RIGHT];
    }

    getToothClass(code) {
        const item = this.payload.teeth[code] || EMPTY_TOOTH();
        const classes = ["o_df_tooth"];
        classes.push("o_df_status_" + (item.status || "healthy"));
        if (this.state.currentToothCode === code) {
            classes.push("o_df_selected");
        }
        return classes.join(" ");
    }

    getToothState(code) {
        return this.payload.teeth[code] || EMPTY_TOOTH();
    }

    async onToothClick(ev) {
        const code = ev.currentTarget.dataset.code;
        this.state.currentToothCode = code;
    }

    async onStatusClick(ev) {
        const status = ev.currentTarget.dataset.status;
        const item = this.payload.teeth[this.state.currentToothCode] || EMPTY_TOOTH();
        item.status = status;
        this.payload.teeth[this.state.currentToothCode] = item;
        await this._updateValue();
    }

    onInputChange() {
        const item = this.payload.teeth[this.state.currentToothCode] || EMPTY_TOOTH();
        const mobilityEl = this.mobilityRef?.el;
        const recessionEl = this.recessionRef?.el;
        const notesEl = this.notesRef?.el;
        if (mobilityEl) item.mobility = mobilityEl.value || "";
        if (recessionEl) item.recession = recessionEl.value || "";
        if (notesEl) item.notes = notesEl.value || "";
        this.payload.teeth[this.state.currentToothCode] = item;
        this._updateValue(false);
    }

    async _updateValue(rerender = true) {
        const newValue = JSON.stringify(this.payload);
        if (this.props.update && newValue !== (this.props.value || "")) {
            if (this.props.setDirty) {
                this.props.setDirty(true);
            }
            await this.props.update(newValue);
        }
        if (rerender) {
            this.state.payload = parsePayload(newValue);
        }
    }

    /** Guardar cambios de la pieza actual (sincroniza con el formulario) */
    async onSaveClick() {
        this.onInputChange();
        await this._updateValue();
    }

    /** Limpiar / resetear la pieza actual a estado sano y campos vacíos */
    async onResetTooth() {
        const code = this.state.currentToothCode;
        this.payload.teeth[code] = EMPTY_TOOTH();
        await this._updateValue();
    }

    /** Estilo del contenedor del panel: si tiene posición guardada, se muestra flotante ahí */
    getInspectorWrapperStyle() {
        const pos = this.state.panelPosition;
        if (!pos) return "";
        return `position: fixed; left: ${pos.left}px; top: ${pos.top}px; z-index: 1050; width: 320px; max-width: 90vw;`;
    }

    /** Inicio de arrastre: pasa a flotante en la posición actual y empieza a seguir el ratón */
    onPanelDragStart(ev) {
        if (ev.button !== 0) return;
        ev.preventDefault();
        const el = this.inspectorWrapperRef?.el;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        let left = rect.left;
        let top = rect.top;
        if (this.state.panelPosition) {
            left = this.state.panelPosition.left;
            top = this.state.panelPosition.top;
        } else {
            this.state.panelPosition = { left, top };
        }
        this.state.dragStart = { x: ev.clientX, y: ev.clientY, left, top };
        document.addEventListener("mousemove", this._boundDragMove);
        document.addEventListener("mouseup", this._boundDragEnd);
        document.body.style.userSelect = "none";
    }

    _onPanelDragMove(ev) {
        if (!this.state.dragStart) return;
        const { x, y, left, top } = this.state.dragStart;
        this.state.panelPosition = {
            left: left + (ev.clientX - x),
            top: Math.max(0, top + (ev.clientY - y)),
        };
    }

    _onPanelDragEnd() {
        this.state.dragStart = null;
        document.removeEventListener("mousemove", this._boundDragMove);
        document.removeEventListener("mouseup", this._boundDragEnd);
        document.body.style.userSelect = "";
    }

    get currentToothState() {
        const payload = this.state.payload;
        if (!payload || !payload.teeth) return EMPTY_TOOTH();
        return payload.teeth[this.state.currentToothCode] || EMPTY_TOOTH();
    }
}

registry.category("fields").add("df_odontogram", OdontogramField, { supportedTypes: ["text"] });

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import uuid

# Initialize ledger CSV if not exists
def init_ledger():
    try:
        df = pd.read_csv('ledger.csv')
    except FileNotFoundError:
        df = pd.DataFrame(columns=["id", "date", "property", "type", "concept", "amount_ars", "amount_usd", "comments"])
        df.to_csv('ledger.csv', index=False)
    return df

# Load or initialize contracts
def load_contracts():
    try:
        with open('contracts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        contracts = {"Alberdi": 35000, "Av. Colón": 40000, "Lote Fortunato": 50000}
        with open('contracts.json', 'w') as f:
            json.dump(contracts, f)
        return contracts

# Load or initialize settings
def load_settings():
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        settings = {"usd_rate": None, "last_updated": None}
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
        return settings

# Save settings
def save_settings(settings):
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

# Format number with thousands separator
def format_number(value):
    return f"{value:,.0f}".replace(",", ".")

# Main App
def main():
    st.title("Gestión de Alquileres y Balance ARS/USD")

    ledger = init_ledger()
    contracts = load_contracts()
    settings = load_settings()

    menu = ["Registrar Movimiento", "Actualizar Contrato", "Actualizar Dólar Blue", "Comprar Dólares", "Ver Balance", "Eliminar Movimiento por ID"]
    choice = st.sidebar.selectbox("Menú", menu)

    if choice == "Registrar Movimiento":
        st.subheader("Registrar Ingreso/Egreso")
        properties = list(contracts.keys()) + ["General"]
        property_choice = st.selectbox("Propiedad", properties)
        tipo = st.selectbox("Tipo", ["Ingreso", "Egreso"])
        date = st.date_input("Fecha del movimiento", value=datetime.now())

        if tipo == "Egreso":
            concept = st.selectbox("Concepto", ["Expensas Alberdi", "Expensas Av. Colón", "ARBA", "Municipalidad", "ABL/Rentas", "VISA", "MasterCard", "Pago por gestión administrativa", "Otro gasto"])
            if concept == "Otro gasto":
                concept_manual = st.text_input("Describir el gasto")
                concept = concept_manual if concept_manual else "Otro gasto"
            amount_ars = st.number_input("Monto ARS", min_value=0.0, format="%.0f")
        else:
            concept = st.selectbox("Concepto", ["Cobro de Alquiler", "Otro ingreso"])
            if concept == "Cobro de Alquiler":
                amount_ars = contracts.get(property_choice, 0)
                st.write(f"Monto automático: {format_number(amount_ars)} ARS")
            else:
                concept_manual = st.text_input("Describir el ingreso")
                concept = concept_manual if concept_manual else "Otro ingreso"
                amount_ars = st.number_input("Monto ARS", min_value=0.0, format="%.0f")

        comments = st.text_area("Comentarios")

        if st.button("Registrar Movimiento"):
            new_row = pd.DataFrame([[str(uuid.uuid4()), date.strftime('%Y-%m-%d'), property_choice, tipo, concept, amount_ars, 0, comments]],
                                   columns=ledger.columns)
            ledger = pd.concat([ledger, new_row], ignore_index=True)
            ledger.to_csv('ledger.csv', index=False)
            st.success("Movimiento registrado")

    elif choice == "Actualizar Contrato":
        st.subheader("Actualizar Valores de Alquiler")
        for prop in contracts:
            new_value = st.number_input(f"Nuevo valor para {prop}", value=contracts[prop], format="%.0f")
            contracts[prop] = new_value
        if st.button("Guardar Contratos"):
            with open('contracts.json', 'w') as f:
                json.dump(contracts, f)
            st.success("Contratos actualizados")

    elif choice == "Actualizar Dólar Blue":
        st.subheader("Actualizar cotización del dólar blue")
        st.write(f"Última cotización registrada: {settings.get('usd_rate')} ARS/USD")
        new_rate = st.number_input("Nuevo valor del dólar blue", min_value=0.0, format="%.2f")
        if st.button("Actualizar Dólar"):
            settings['usd_rate'] = new_rate
            settings['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            save_settings(settings)
            st.success("Dólar actualizado")

    elif choice == "Comprar Dólares":
        st.subheader("Comprar Dólares con ARS")
        total_ars = ledger[ledger['type'] == 'Ingreso']['amount_ars'].sum() - ledger[ledger['type'] == 'Egreso']['amount_ars'].sum()
        st.write(f"Balance disponible ARS: {format_number(total_ars)}")
        st.info("Debe ingresar la cotización del dólar blue (verificar en dolarhoy.com)")

        usd_rate = st.number_input("Cotización ARS/USD (obligatoria)", min_value=0.0, format="%.2f")
        ars_to_use = st.number_input("Monto ARS a usar", min_value=0.0, max_value=float(total_ars), format="%.0f")

        if st.button("Comprar Dólares"):
            if usd_rate == 0:
                st.error("La cotización es obligatoria")
            else:
                usd_bought = ars_to_use / usd_rate
                new_row = pd.DataFrame([[str(uuid.uuid4()), datetime.now().strftime('%Y-%m-%d'), "General", "Egreso", "Compra de dólares", ars_to_use, usd_bought, ""]],
                                       columns=ledger.columns)
                ledger = pd.concat([ledger, new_row], ignore_index=True)
                ledger.to_csv('ledger.csv', index=False)
                st.success(f"Compra registrada: {format_number(ars_to_use)} ARS por {usd_bought:.2f} USD")

    elif choice == "Ver Balance":
        st.subheader("Balance y Historial")
        st.write("Movimientos registrados:")
        st.dataframe(ledger)

        total_ingresos = ledger[ledger['type'] == 'Ingreso']['amount_ars'].sum()
        total_egresos = ledger[ledger['type'] == 'Egreso']['amount_ars'].sum()
        balance_ars = total_ingresos - total_egresos

        st.write(f"**Total Ingresos ARS:** {format_number(total_ingresos)}")
        st.write(f"**Total Egresos ARS:** {format_number(total_egresos)}")
        st.write(f"**Balance en ARS:** {format_number(balance_ars)}")

        if settings.get('usd_rate'):
            balance_usd = balance_ars / settings['usd_rate']
            st.write(f"**Balance estimado en USD:** {balance_usd:.2f} USD")

    elif choice == "Eliminar Movimiento por ID":
        st.subheader("Eliminar Movimiento por ID")
        st.write("Listado de movimientos con ID único")
        st.dataframe(ledger[['id', 'date', 'property', 'type', 'concept', 'amount_ars']])
        id_to_delete = st.text_input("Ingrese el ID del movimiento a eliminar")

        if st.button("Eliminar seleccionado"):
            if id_to_delete in ledger['id'].values:
                ledger = ledger[ledger['id'] != id_to_delete]
                ledger.to_csv('ledger.csv', index=False)
                st.success("Movimiento eliminado")
            else:
                st.warning("ID no encontrado")

if __name__ == "__main__":
    main()

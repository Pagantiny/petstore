import mysql.connector
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session, make_response
import csv
import io
import pandas as pd

from matplotlib import pyplot as plt

USERNAME = "admin"
PASSWORD = "password"

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Usato per firmare la sessione

# Configurazione del database
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="yourpassword",
  database="pydb")



mycursor = mydb.cursor()
query = "SELECT id, nome, marca, pezzi, pezzivenduti  FROM petstore"
mycursor.execute(query)
myresult1 = mycursor.fetchall()
# Ottenere i nomi delle colonne
column_names = [desc[0] for desc in mycursor.description]

# Creare un DataFrame Pandas con i nomi delle colonne
df = pd.DataFrame(myresult1, columns=column_names)
#print(df)

sommaP = df['pezzi'].sum()
sommaV = df['pezzivenduti'].sum()
mediaP = df['pezzi'].mean()
mediaV = df['pezzivenduti'].mean()
#print(sommaP, sommaV)

new_row = {
    'id': "",  # Imposta su NaN o su un valore predefinito
    'nome': "",  # Imposta su NaN o su un valore predefinito
    'marca': "Somma",  # Imposta su NaN o su un valore predefinito
    'pezzi': sommaP,  # Valore specificato
    'pezzivenduti': sommaV  # Valore specificato
}

new_row2 = {
    'id': "",  # Imposta su NaN o su un valore predefinito
    'nome': "",  # Imposta su NaN o su un valore predefinito
    'marca': "Media",  # Imposta su NaN o su un valore predefinito
    'pezzi': mediaP,
    'pezzivenduti': mediaV

}

## Creare un DataFrame dalla nuova riga
new_row_df = pd.DataFrame([new_row])
new_row2_df = pd.DataFrame([new_row2])

# Aggiungere la nuova riga usando pd.concat
df = pd.concat([df, new_row_df], ignore_index=True)
df = pd.concat([df, new_row2_df], ignore_index=True)


lista_prodotti = df.values.tolist()
print(lista_prodotti)


@app.route('/dati_vendita')
def dati_vendita():
    lista_prodotti = df.values.tolist()

    # Calcolare il prodotto più venduto
    index_max = df['pezzivenduti'].idxmax()  # Ottieni l'indice del valore massimo
    index_min = df['pezzivenduti'].idxmin()

    # Calcolare l'indice del prodotto più venduto, escludendo l'ultima riga
    index_max = df['pezzivenduti'][:-2].idxmax()  # Prende solo le righe fino all'ultima
    prodotto_piu_venduto = df.loc[index_max]
    prodotto_max = prodotto_piu_venduto['nome']


    index_max = df['pezzivenduti'][:-2].idxmin()
    prodotto_piu_venduto = df.loc[index_min]
    prodotto_min = prodotto_piu_venduto['nome']

    return render_template('dati_vendita.html', lista=lista_prodotti, prodottoMax=prodotto_max, prodottoMin=prodotto_min)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifica le credenziali dell'utente
        if username == USERNAME and password == PASSWORD:
            session['user'] = username  # Memorizza l'utente nella sessione
            return redirect(url_for('gestore'))  # Reindirizza all'area protetta
        else:
            return "Credenziali non valide"

    return render_template("login.html")

@app.route('/')
def home():
    return redirect(url_for('store'))
@app.route('/gestore',methods=['POST', 'GET'])
def gestore():
    if 'user' in session:
        mycursor = mydb.cursor()

        mycursor.execute("SELECT * FROM petstore")

        myresult = mycursor.fetchall()
        listaD = []
        for i in myresult:
            listaD.append(i[2])

        listaS = list(dict.fromkeys(listaD))


        return render_template("gestore.html", lista=myresult, listaS=listaS)
    else:
        return redirect(url_for('login'))

@app.route('/prodotti/<categoria>')
def prodotti_categoria(categoria):

    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM petstore WHERE categoria = %s", (categoria,))
    prodotti = mycursor.fetchall()

    return render_template('prodotti_categoria.html', prodotti=prodotti)

@app.route('/export_csv', methods=['POST'])
def export_csv():
    # Esegui la query per selezionare tutti i prodotti
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM petstore")
    myresult = mycursor.fetchall()
    print(myresult)

    # Nome del file CSV
    file_csv = 'prodotti.csv'


    # Scrivi i dati nel file CSV
    with open(file_csv, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Scrivi l'intestazione (modifica in base alle tue colonne)
        writer.writerow(['ID', 'Nome', 'Marca', 'Prezzo','categoria', 'URL', 'Pezzi', 'pezzivenduti'])

        # Scrivi i dati
        writer.writerows(myresult)

    print(f"File {file_csv} creato con successo!")
    return redirect(url_for('gestore'))

# Rotta per visualizzare i prodotti nello store
@app.route('/store', methods=['GET', 'POST'])
def store():
    mycursor = mydb.cursor()

    # Query per prendere tutti i prodotti
    mycursor.execute("SELECT ID, Nome, Marca, Prezzo, URL FROM petstore")
    prodotti = mycursor.fetchall()


    # Aggiungere prodotti al carrello
    if request.method == 'POST':
        selected_products = request.form.getlist('prodotti_selezionati')

        # Inizializza il carrello nella sessione se non esiste
        if 'cart' not in session:
            session['cart'] = []

        # Aggiungere prodotti selezionati al carrello
        for product_id in selected_products:
            if product_id not in session['cart']:
                session['cart'].append(product_id)

        # Salva la sessione
        session.modified = True

        return redirect(url_for('cart'))

    # Modalità di visualizzazione (card, tabella, lista)
    view_mode = request.args.get('view', 'card')  # Default 'card'

    return render_template('store.html', prodotti=prodotti, view_mode=view_mode)

# Rotta per visualizzare il carrello
@app.route('/cart')
def cart():
    if 'cart' not in session or len(session['cart']) == 0:
        return "Il tuo carrello è vuoto!"

    mycursor = mydb.cursor()

    # Recupera i prodotti nel carrello
    cart_products_ids = session['cart']
    format_strings = ','.join(['%s'] * len(cart_products_ids))
    mycursor.execute(f"SELECT ID, Nome, Marca, Prezzo, URL FROM petstore WHERE ID IN ({format_strings})", tuple(cart_products_ids))
    cart_products = mycursor.fetchall()

    # Calcola il prezzo totale
    total_price = sum([product[3] for product in cart_products])


    return render_template('cart.html', prodotti=cart_products, total_price=total_price)

# Rotta per rimuovere un prodotto dal carrello
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'].remove(str(product_id))
        session.modified = True
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['POST'])
def checkout():
    if 'cart' not in session or not session['cart']:
        return redirect(url_for('store'))

    mycursor = mydb.cursor()

    # Per ogni prodotto nel carrello
    for product_id in session['cart']:
        # Recupera il numero di pezzi selezionati
        quantity = request.form.get(f'quantity_{product_id}', 1)

        # Aggiorna la tabella MySQL: decrementa 'Pezzi' e incrementa 'pezzivenduti'
        mycursor.execute("""
            UPDATE petstore 
            SET Pezzi = Pezzi - %s, pezzivenduti = pezzivenduti + %s 
            WHERE ID = %s AND Pezzi >= %s
        """, (quantity, quantity, product_id, quantity))

    # Effettua il commit delle modifiche nel database
    mydb.commit()

    # Svuota il carrello dopo il checkout
    session.pop('cart', None)

    return render_template('checkout_success.html')  # Pagina di conferma acquisto


@app.route('/combined_chart.png')
def plot_png():
    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM petstore")

    prodotti = mycursor.fetchall()

    # Estrai le etichette (colonna [1]) e vendite (colonna [7]) dalle tuple
    etichette = [row[1] for row in prodotti]  # Supponiamo che row[1] sia il nome del prodotto
    vendite = [row[6] for row in prodotti]  # Sup

    # Crea una figura con due subplot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))  # 1 riga, 2 colonne

    # --- Grafico a barre ---
    ax1.bar(etichette, vendite, color='skyblue')
    ax1.set_title('Vendite per Prodotto (Grafico a Barre)')
    ax1.set_ylabel('Vendite')

    # --- Grafico a torta ---
    ax2.pie(vendite, labels=etichette, autopct='%1.1f%%', startangle=90, colors=['#ff9999', '#66b3ff', '#99ff99'])
    ax2.axis('equal')  # Per mantenere la torta circolare
    ax2.set_title('Distribuzione Vendite (Grafico a Torta)')

    # Salva la figura in memoria come PNG
    output = io.BytesIO()
    fig.savefig(output, format='png')
    plt.close(fig)
    output.seek(0)

    return make_response(output.getvalue(), 200, {'Content-Type': 'image/png'})

if __name__ == '__main__':
    app.run(debug=True)


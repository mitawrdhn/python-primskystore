from flask import Flask, render_template, session, request, redirect, url_for, g, flash
from flask_mysqldb import MySQL, MySQLdb
MySQLdb.paramstyle
import bcrypt
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired



import os
import pickle
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.metrics import davies_bouldin_score

#visualizations
import matplotlib.pyplot as plt


app = Flask (__name__)
app.secret_key = os.urandom(24)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'pos'
# app.config['SECRET_KEY'] = 'supersecretkey'
# app.config['UPLOAD_FOLDER'] = 'static/files'
mysql = MySQL(app)


# class UploadFileForm(FlaskForm):
#     file = FileField("File", validators=[InputRequired()])
#     submit = SubmitField("Upoload File")

# @app.route("/", methods=['GET',"POST"])
# @app.route("/home", methods=['GET',"POST"])
# def home():
#     form= UploadFileForm()
#     if form.validate_on_submit():
#         file = form.file.data #first grab the file
#         file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], secure_filename(file.filename))) #then save the file
#         return "File has been upoaded."
#     return render_template('index.html', form=form)

# if __name__ == '__main__':
#     app.run(debug=True)

@app.route("/", methods=['GET', 'POST'])
def main():
    return render_template('login.html')

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    conn = mysql.connection.cursor()
    conn.execute("SELECT count(distinct(nomor_invoice)),count(distinct(nama_pembeli)),count(distinct(nama_produk)), ROUND(sum((jumlah_produk_dibeli*harga_jual)/180),0) FROM data_penjualan")
    sales = conn.fetchall()
    #count cluster
    conn.execute("SELECT COUNT(nama_produk), cluster FROM data_cluster GROUP BY cluster ASC;")
    cluster = conn.fetchall()
    conn.execute("SELECT ROUND(AVG(recency),3),ROUND(AVG(frequency),3), ROUND(AVG(monetary),3), cluster FROM `data_cluster` group by cluster asc;")
    cluster1 = conn.fetchall()
    conn.close()
    return render_template('home.html',menu='dashboard', data=sales, data1=cluster, data2=cluster1)

@app.route("/manage", methods=['GET', 'POST'])
def manage():
    conn = mysql.connection.cursor()
    conn.execute("SELECT id,nama_toko,deskripsi FROM data_toko")
    informasi = conn.fetchall()
    conn.execute("SELECT distinct(pertanyaan) FROM data_keterangan")
    pertanyaan = conn.fetchall()
    conn.execute("SELECT id,jawaban FROM data_keterangan")
    jawaban = conn.fetchall()
    conn.close()
    return render_template('kelolainformasi.html',menu='manage', data=informasi, data1=pertanyaan,data2=jawaban)

@app.route('/edit_datatoko/<string:id>', methods = ['GET'])
def edit_toko(id):
    conn = mysql.connection.cursor()
    conn.execute("SELECT nama_toko,deskripsi,id FROM data_toko WHERE id = %s", (id,))
    informasi = conn.fetchall()
    conn.close()
    return render_template('edit_datatoko.html', menu='manage', data=informasi)

@app.route('/simpaneditdatatoko/<int:id>', methods=['POST', 'GET'])
def simpaneditdatatoko(id):
    if request.method == 'POST':
        #post
        conn = mysql.connection.cursor()
        nama_toko = request.form['nama_toko']
        deskripsi = request.form['deskripsi']
        #koneksi
        sql=f"UPDATE `data_toko` SET `nama_toko`=\'{nama_toko}\',`deskripsi`=\'{deskripsi}\' WHERE `id`={id}"
        conn.execute(sql)
        mysql.connection.commit()
        conn.close()
    return redirect(url_for('manage'))

@app.route('/edit_datapertanyaan', methods = ['GET'])
def edit_datapertanyaan():
    conn = mysql.connection.cursor()
    conn.execute("SELECT distinct(pertanyaan) FROM data_keterangan")
    pertanyaan = conn.fetchall()
    conn.close()
    return render_template('edit_datapertanyaan.html', menu='manage', data=pertanyaan)

@app.route('/simpaneditdatapertanyaan', methods=['POST', 'GET'])
def simpaneditdatapertanyaan():
    if request.method == 'POST':
        #post
        conn = mysql.connection.cursor()
        pertanyaan = request.form['pertanyaan']
        #koneksi
        sql=f"UPDATE `data_keterangan` SET `pertanyaan`=\'{pertanyaan}\'"
        conn.execute(sql)
        mysql.connection.commit()
        conn.close()
    return redirect(url_for('manage'))

@app.route('/edit_datajawaban/<string:id>', methods = ['GET'])
def edit_datajawaban(id):
    conn = mysql.connection.cursor()
    conn.execute("SELECT pertanyaan,jawaban,id FROM data_keterangan WHERE id = %s", (id,))
    jawaban = conn.fetchall()
    conn.close()
    return render_template('edit_datajawaban.html', menu='manage', data=jawaban)

@app.route('/simpaneditdatajawaban/<int:id>', methods=['POST', 'GET'])
def simpaneditdatajawaban(id):
    if request.method == 'POST':
        #post
        conn = mysql.connection.cursor()
        jawaban = request.form['jawaban']
        #koneksi
        sql=f"UPDATE `data_keterangan` SET `jawaban`=\'{jawaban}\' WHERE `id`={id}"
        conn.execute(sql)
        mysql.connection.commit()
        conn.close()
    return redirect(url_for('manage'))

#admin
@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = mysql.connection.cursor()
    msg = ''
    # cek username password
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        conn.execute('SELECT * FROM data_admin WHERE username = %s AND password = %s', (username, password))
        account = conn.fetchone()
   
        # if cek akun valid
        if account:
            # session data
            session['loggedin'] = True
            session['username'] = username
            flash("Login Berhasil")
            return redirect(url_for('dashboard'))
        # akun tidak valid
        else:
            flash("Username / Password Salah!")
    return render_template('login.html', msg=msg)


# @app.route("/protected")
# def protected():
#     if g.user:
#         return render_template('index.html', user=session['user'])
#     return redirect(url_for('main'))

@app.route("/index")
def index():
    conn = mysql.connection.cursor()
    conn.execute("SELECT nama_toko,deskripsi FROM data_toko")
    informasi = conn.fetchall()
    conn.execute("SELECT nama, harga FROM data_produk")
    produk = conn.fetchall()
    conn.execute("SELECT distinct(pertanyaan) FROM data_keterangan")
    pertanyaan = conn.fetchall()
    conn.execute("SELECT jawaban,id FROM data_keterangan")
    jawaban = conn.fetchall()
    conn.close()
    return render_template('index.html', data=produk, data1=informasi, data2=pertanyaan, data3=jawaban)

@app.route("/dropsession")
def dropsession():
    session.pop('user', None)
    return render_template('login.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        nama = request.form['nama']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO data_admin VALUES (%s,%s,%s,%s)", (nama,email,username,password,))
        mysql.connection.commit()
        return redirect(url_for('login'))


@app.route("/masterbarang")
def masterbarang():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nama, harga FROM data_produk")
    # cur.execute("SELECT id_produk,nama, harga, deskripsi, foto FROM data_produk;")
    produk = cur.fetchall()
    cur.close()
    return render_template('masterbarang.html', menu='master',submenu='barang', data=produk)

@app.route("/formmasterbarang")
def formmasterbarang():
    cur = mysql.connection.cursor()
    cur.execute("SELECT max(id)+1 FROM `data_produk`")
    newid = cur.fetchall()
    cur.close()
    return render_template('formmasterbarang.html', menu='master',submenu='barang',data=newid)

@app.route("/simpanformmasterbarang", methods=["POST"])
def simpanformmasterbarang():  
    #post
    id = request.accept_charsets['id']
    nama = request.form['nama']
    harga = request.form['harga']
    #koneksi
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO data_produk VALUES (%s,%s,%s)", (nama, harga,id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('masterbarang'))

@app.route('/view_dataproduk/<id>', methods = ['POST', 'GET'])
def view_produk(id):
    conn = mysql.connection.cursor()
    conn.execute("SELECT nama,harga FROM data_produk WHERE id = %s", (id,))
    produk = conn.fetchall()
    conn.close()
    return render_template('view_dataproduk.html', menu='master',submenu='barang', data=produk)

@app.route('/edit_dataproduk/<string:id>', methods = ['GET'])
def edit_produk(id):
    conn = mysql.connection.cursor()
    conn.execute("SELECT nama,harga,id FROM data_produk WHERE id = %s", (id,))
    produk = conn.fetchall()
    conn.close()
    return render_template('edit_dataproduk.html', menu='master',submenu='barang', data=produk)

@app.route('/simpaneditformdataproduk/<int:id>', methods=['POST', 'GET'])
def simpaneditformdataproduk(id):
    if request.method == 'POST':
        #post
        conn = mysql.connection.cursor()
        nama_produk = request.form['nama_produk']
        harga = request.form['harga']
        #koneksi
        sql=f"UPDATE `data_produk` SET `nama`=\'{nama_produk}\',`harga`=\'{harga}\' WHERE `id`={id}"
        conn.execute(sql)
        mysql.connection.commit()
        conn.close()
        flash("Data Updated")
        
    return redirect(url_for('masterbarang'))

@app.route('/delete_dataproduk/<id>', methods = ['POST', 'GET'])
def delete_produk(id):
    conn = mysql.connection.cursor()
    conn.execute("DELETE FROM data_produk WHERE id = %s", (id,))
    mysql.connection.commit()
    conn.close()
    return redirect(url_for('masterbarang'))

@app.route("/masterpelanggan")
def masterpelanggan():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT nama_pembeli, no_telp_pembeli, kota, provinsi FROM data_penjualan;")
    pelanggan = cur.fetchall()
    cur.close()
    return render_template('masterpelanggan.html',menu='master',submenu='pelanggan', data=pelanggan)

@app.route("/formmasterpelanggan")
def formmasterpelanggan():
    return render_template('formmasterpelanggan.html', menu='master',submenu='pelanggan')

@app.route("/simpanformmasterpelanggan", methods=["POST"])
def simpanformmasterpelanggan():  
    #post
    nama = request.form['nama']
    alamat = request.form['alamat']
    kota = request.form['kota']
    #koneksi
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO masterpelanggan(nama,alamat,kota) VALUES(%s,%s,%s)", (nama,alamat,kota))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('masterpelanggan'))

@app.route("/formdatapenjualan")
def formdatapenjualan():
    #koneksi
    cur = mysql.connection.cursor()
    cur.execute("SELECT max(id)+1 FROM `data_penjualan`")
    newid = cur.fetchall()
    cur.execute("SELECT kode,nama FROM wilayah_2022 WHERE CHAR_LENGTH(kode)=2 ORDER BY nama;")
    provinsi = cur.fetchall()
    cur.execute("SELECT DISTINCT(nama_kurir) FROM data_penjualan ORDER BY nama_kurir;")
    kurir = cur.fetchall()
    cur.execute("SELECT nama FROM data_produk ORDER BY nama;")
    produk = cur.fetchall()
    cur.close()
    return render_template('formdatapenjualan.html', menu='penjualan',submenu='formpenjualan', data=newid, data1=provinsi, data2=kurir, data3=produk)

@app.route("/simpanformdatapenjualan", methods=["POST"])
def simpanformdatapenjualan():  
    #post
    id = request.accept_charsets['id']
    nomor_invoice = request.form['nomor_invoice']
    tanggal_pembayaran = request.form['tanggal_pembayaran']
    status_terakhir = request.form['status_terakhir']
    nama_produk = request.form['nama_produk']
    jumlah_produk_dibeli = request.form['jumlah_produk_dibeli']
    harga_jual = request.form['harga_jual']
    nama_pembeli = request.form['nama_pembeli']
    no_telp_pembeli = request.form['no_telp_pembeli']
    nama_penerima = request.form['nama_penerima']
    no_telp_penerima = request.form['no_telp_penerima']
    alamat_pengiriman = request.form['alamat_pengiriman']
    kota = request.form['kota']
    provinsi = request.form['provinsi']
    nama_kurir = request.form['nama_kurir']
    no_resi_kode_booking = request.form['no_resi_kode_booking']
    #koneksi
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO data_penjualan VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (nomor_invoice,tanggal_pembayaran,status_terakhir,nama_produk,jumlah_produk_dibeli,harga_jual,nama_pembeli,no_telp_pembeli,nama_penerima,no_telp_penerima,alamat_pengiriman,kota,provinsi,nama_kurir,no_resi_kode_booking,id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('datapenjualan'))

def formpenjualan():
    return render_template('formdatapenjualan.html', menu='penjualan',submenu='formpenjualan')

@app.route("/datapenjualan")
def datapenjualan():
    conn = mysql.connection.cursor()
    conn = mysql.connection.cursor()
    conn.execute("SELECT id, nomor_invoice, nama_produk, sum(jumlah_produk_dibeli*harga_jual) as total, nama_pembeli, no_resi_kode_booking FROM data_penjualan group by id")
    penjualan = conn.fetchall()
    conn.close()
    return render_template('datapenjualan.html', menu='penjualan',submenu='datapenjualan', data=penjualan)

@app.route('/view_datapenjualan/<no_resi_kode_booking>', methods = ['POST', 'GET'])
def view_penjualan(no_resi_kode_booking):
    conn = mysql.connection.cursor()
    conn.execute("SELECT `tanggal_pembayaran`,`nomor_invoice`, `nama_produk`, sum(jumlah_produk_dibeli*harga_jual) as total, `nama_pembeli`, `no_resi_kode_booking`, kota, provinsi, alamat_pengiriman, no_telp_pembeli, count(id), CURRENT_TIMESTAMP 'date', no_resi_kode_booking FROM data_penjualan WHERE no_resi_kode_booking = %s", (no_resi_kode_booking,))
    penjualan = conn.fetchall()
    conn.execute("SELECT id, nama_produk, jumlah_produk_dibeli, harga_jual, jumlah_produk_dibeli*harga_jual as total FROM data_penjualan WHERE no_resi_kode_booking = %s GROUP BY id", (no_resi_kode_booking,))
    barang = conn.fetchall()
    conn.close()
    return render_template('view_datapenjualan.html', menu='penjualan',submenu='datapenjualan', data=penjualan, data1=barang)
  
@app.route('/edit_datapenjualan/<string:id>', methods = ['GET'])
def edit_penjualan(id):
    conn = mysql.connection.cursor()
    conn.execute("SELECT nomor_invoice,tanggal_pembayaran,status_terakhir,nama_produk,jumlah_produk_dibeli,harga_jual,nama_pembeli,no_telp_pembeli,nama_penerima,no_telp_penerima,alamat_pengiriman,kota,provinsi,nama_kurir,no_resi_kode_booking,id FROM data_penjualan WHERE id = %s", (id,))
    penjualan = conn.fetchall()
    conn.close()
    return render_template('edit_datapenjualan.html', menu='penjualan',submenu='datapenjualan', data=penjualan)

@app.route('/simpaneditformdatapenjualan/<int:id>', methods=['POST', 'GET'])
def simpaneditformdatapenjualan(id):
    if request.method == 'POST':
        #post
        conn = mysql.connection.cursor()
        nomor_invoice = request.form['nomor_invoice']
        tanggal_pembayaran = request.form['tanggal_pembayaran']
        status_terakhir = request.form['status_terakhir']
        nama_produk = request.form['nama_produk']
        jumlah_produk_dibeli = request.form['jumlah_produk_dibeli']
        harga_jual = request.form['harga_jual']
        nama_pembeli = request.form['nama_pembeli']
        no_telp_pembeli = request.form['no_telp_pembeli']
        nama_penerima = request.form['nama_penerima']
        no_telp_penerima = request.form['no_telp_penerima']
        alamat_pengiriman = request.form['alamat_pengiriman']
        kota = request.form['kota']
        provinsi = request.form['provinsi']
        nama_kurir = request.form['nama_kurir']
        no_resi_kode_booking = request.form['no_resi_kode_booking']
        #koneksi
        # sql=f"UPDATE `data_penjualan` SET `nomor_invoice`=\'{nomor_invoice}\' WHERE `id`={id}"
        sql=f"UPDATE `data_penjualan` SET `nomor_invoice`=\'{nomor_invoice}\',`tanggal_pembayaran`=\'{tanggal_pembayaran}\',`status_terakhir`=\'{status_terakhir}\',`nama_produk`=\'{nama_produk}\',`jumlah_produk_dibeli`=\'{jumlah_produk_dibeli}\',`harga_jual`=\'{harga_jual}\',`nama_pembeli`=\'{nama_pembeli}\',`no_telp_pembeli`=\'{no_telp_pembeli}\',`nama_penerima`=\'{nama_penerima}\',`no_telp_penerima`=\'{no_telp_penerima}\',`alamat_pengiriman`=\'{alamat_pengiriman}\',`kota`=\'{kota}\',`provinsi`=\'{provinsi}\',`nama_kurir`=\'{nama_kurir}\',`no_resi_kode_booking`=\'{no_resi_kode_booking}\' WHERE `id`={id}"
        conn.execute(sql)
        sql1=f"UPDATE `data_penjualan` SET `nomor_invoice`=\'{nomor_invoice}\',`tanggal_pembayaran`=\'{tanggal_pembayaran}\',`status_terakhir`=\'{status_terakhir}\',`nama_pembeli`=\'{nama_pembeli}\',`no_telp_pembeli`=\'{no_telp_pembeli}\',`nama_penerima`=\'{nama_penerima}\',`no_telp_penerima`=\'{no_telp_penerima}\',`alamat_pengiriman`=\'{alamat_pengiriman}\',`kota`=\'{kota}\',`provinsi`=\'{provinsi}\',`nama_kurir`=\'{nama_kurir}\',`no_resi_kode_booking`=\'{no_resi_kode_booking}\' WHERE `no_resi_kode_booking`=\'{no_resi_kode_booking}\'"
        conn.execute(sql1)
        mysql.connection.commit()
        conn.close()
        flash("Data Updated")
        
    return redirect(url_for('datapenjualan'))

@app.route('/delete_datapenjualan/<id>', methods = ['POST', 'GET'])
def delete_penjualan(id):
    conn = mysql.connection.cursor()
    conn.execute("DELETE FROM data_penjualan WHERE id = %s", (id,))
    mysql.connection.commit()
    conn.close()
    return redirect(url_for('datapenjualan'))

@app.route("/hasilrfm")
def hasilrfm():
    cur = mysql.connection.cursor()
    cur.execute("SELECT Nama_Produk AS Produk, TIMESTAMPDIFF(DAY,MAX(Tanggal_Pembayaran),'2022-06-30') AS Recency, COUNT(Nomor_Invoice) AS Frequency, SUM(Jumlah_Produk_Dibeli*Harga_Jual) AS Monetary FROM data_penjualan GROUP BY Nama_Produk;")
    rfm = cur.fetchall()
    cur.close()
    return render_template('hasilrfm.html', menu='perhitungan',submenu='hasilrfm', data=rfm)

@app.route("/normalisasirfm")
def normalisasirfm():
    cur = mysql.connection.cursor()
    #code rfm
    cur.execute("SELECT Nama_Produk AS Produk, TIMESTAMPDIFF(DAY,MAX(Tanggal_Pembayaran),'2022-06-30') AS Recency, COUNT(Nomor_Invoice) AS Frequency, SUM(Jumlah_Produk_Dibeli*Harga_Jual) AS Monetary FROM data_penjualan GROUP BY Nama_Produk;")
    df = pd.DataFrame(cur.fetchall(), columns=['Produk', 'Recency', 'Frequency', 'Monetary'])

    #code normalisasi
    def Nor_Recency(row):
        x=((row['Recency']-min(df['Recency']))/(max(df['Recency'])-min(df['Recency'])))*(1-0)+0
        return x

    def Nor_Frequency(row):
        y=((row['Frequency']-min(df['Frequency']))/(max(df['Frequency'])-min(df['Frequency'])))*(1-0)+0
        return y
  
    def Nor_Monetary(row):
        z=((row['Monetary']-min(df['Monetary']))/(max(df['Monetary'])-min(df['Monetary'])))*(1-0)+0
        return z

#normalisasi ke df
    df['Nor_Recency']=df.apply(lambda row: Nor_Recency(row), axis=1,result_type="expand")
    df['Nor_Frequency']=df.apply(lambda row: Nor_Frequency(row), axis=1,result_type="expand")
    df['Nor_Monetary']=df.apply(lambda row: Nor_Monetary(row), axis=1,result_type="expand")

#drop RRFM asli
    df = df.drop(['Recency'], axis=1)
    df = df.drop(['Frequency'], axis=1)
    df = df.drop(['Monetary'], axis=1)

#
#hasil normalisasi
    nor = (df['Produk'], df['Nor_Recency'], df['Nor_Frequency'], df['Nor_Monetary'])
    array = np.array(nor)
    transposed_array = array.T
    res = transposed_array.tolist()
    # This is the same as: transposed = np.array(list_of_lists).T.tolist()
    return render_template('normalisasirfm.html', menu='perhitungan',submenu='normalisasirfm', data=res)

@app.route("/kmeans")
def kmeans():
    cur = mysql.connection.cursor()
    #code rfm
    cur.execute("SELECT Nama_Produk AS Produk, TIMESTAMPDIFF(DAY,MAX(Tanggal_Pembayaran),'2022-06-30') AS Recency, COUNT(Nomor_Invoice) AS Frequency, CONVERT(SUM(Jumlah_Produk_Dibeli*Harga_Jual), INT) AS Monetary FROM data_penjualan GROUP BY Nama_Produk;")
    df = pd.DataFrame(cur.fetchall(), columns=['Produk', 'Recency', 'Frequency', 'Monetary'])

    #code normalisasi
    def Nor_Recency(row):
        x=((row['Recency']-min(df['Recency']))/(max(df['Recency'])-min(df['Recency'])))*(1-0)+0
        return x

    def Nor_Frequency(row):
        y=((row['Frequency']-min(df['Frequency']))/(max(df['Frequency'])-min(df['Frequency'])))*(1-0)+0
        return y
  
    def Nor_Monetary(row):
        z=((row['Monetary']-min(df['Monetary']))/(max(df['Monetary'])-min(df['Monetary'])))*(1-0)+0
        return z

#normalisasi ke df
    df['Nor_Recency']=df.apply(lambda row: Nor_Recency(row), axis=1)
    df['Nor_Frequency']=df.apply(lambda row: Nor_Frequency(row), axis=1)
    df['Nor_Monetary']=df.apply(lambda row: Nor_Monetary(row), axis=1)

#drop RRFM asli
    df = df.drop(['Recency'], axis=1)
    df = df.drop(['Frequency'], axis=1)
    df = df.drop(['Monetary'], axis=1)

#

####################
#clustering
    z = df.iloc[:, [1,2,3]].values
    selected_cols = ["Produk", "Nor_Recency", "Nor_Frequency", "Nor_Monetary"]
    cluster_data = df.loc[:, selected_cols]
    kmeans_s = KMeans(n_clusters=3, random_state=0).fit(z)
    label = pd.DataFrame(kmeans_s.labels_)
    clustered_data = cluster_data.assign(cluster=label)
    clustered_data['Nor_Recency'] = clustered_data['Nor_Recency'].round(5)
    clustered_data['Nor_Frequency'] = clustered_data['Nor_Frequency'].round(5)
    clustered_data['Nor_Monetary'] = clustered_data['Nor_Monetary'].round(5)
    clustered_data = tuple(clustered_data.itertuples(index=False, name=None))


    # #jumlah data tiap cluster
    # cluster_0 = clustered_data[clustered_data['cluster']==0]['Produk'].count()
    # cluster_1 = clustered_data[clustered_data['cluster']==1]['Produk'].count()
    # cluster_2 = clustered_data[clustered_data['cluster']==2]['Produk'].count()

    # #centroid
    # grouped_km = clustered_data.groupby(['cluster']).mean().round(1)
    # grouped_km2 = clustered_data.groupby(['cluster']).mean().round(1).reset_index()
    # grouped_km2['cluster'] = grouped_km2['cluster'].map(str)
    # grouped_km2 = tuple(grouped_km2.itertuples(index=False, name=None))
    # data_cluster = [cluster_0, cluster_1, cluster_2]

#hasil normalisasi
    
    # This is the same as: transposed = np.array(list_of_lists).T.tolist()
    #hasil 
    # data_cluster=data_cluster,grouped_km2=grouped_km2
    return render_template('kmeans.html', menu='perhitungan',submenu='kmeans', label=label, data=clustered_data)

@app.route('/produkcluster/<cluster>', methods = ['POST', 'GET'])
def produkcluster(cluster):
    conn = mysql.connection.cursor()
    conn.execute("SELECT DISTINCT(cluster) from data_cluster WHERE cluster = %s", (cluster,))
    nomer = conn.fetchall()
    conn.execute("SELECT nama_produk,cluster from data_cluster WHERE cluster = %s", (cluster,))
    cluster = conn.fetchall()
    
    conn.close()
    return render_template('produkcluster.html', menu='perhitungan',submenu='hasilrfm', data=cluster, data1=nomer)

@app.route("/metodeelbow")
def metodeelbow():
    cur = mysql.connection.cursor()
    cur.execute("SELECT TIMESTAMPDIFF(DAY,MAX(Tanggal_Pembayaran),'2022-06-30') AS Recency, COUNT(Nomor_Invoice) AS Frequency, SUM(Jumlah_Produk_Dibeli*Harga_Jual) AS Monetary FROM data_penjualan GROUP BY Nama_Produk;")
    rfm = cur.fetchall()
    scaler = MinMaxScaler()
    nor_daf=scaler.fit_transform(rfm)
    # ELBOW METHOD
    plt.figure(figsize=(8,5))
    K = range(1,10)
    Sum_of_squared_distances = []
    for k in K:
        km = KMeans(n_clusters=k)
        km = km.fit(nor_daf)
        Sum_of_squared_distances.append(km.inertia_)
    plt.plot(K, Sum_of_squared_distances, 'bx-', color='black', marker='o',markersize=6)
    plt.xlabel('No of Clusters')
    plt.ylabel('Sum_of_squared_distances')
    plt.title('Elbow Method For Optimal k')
    number_of_clusters = 3 #define it after check the elbow
    plt.axvline(x=number_of_clusters, color='blue',linestyle='--')  
    return render_template('metodeelbow.html', menu='clustering',submenu='metodeelbow')

@app.route("/metodesilhouette")
def metodesilhouette():
    
    return render_template('metodesilhouette.html', menu='clustering',submenu='metodesilhouette')

if __name__ == "__main__":
    app.run(debug=True)


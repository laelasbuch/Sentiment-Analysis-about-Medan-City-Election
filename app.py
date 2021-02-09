from flask import Flask, render_template, jsonify, request, url_for, redirect, session
import pandas as pd
import re
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import mysql.connector
import json

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import confusion_matrix


app = Flask(__name__)
app.secret_key = 'any random string'

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="skripsiasbuch"
)

@app.route("/keluar")
def keluar():
    session.pop("admin",None)
    return redirect(url_for("index"))

@app.route("/", methods=["GET","POST"])
def index():
    if 'admin' in session:
        return redirect(url_for("dashboard"))
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        if len(username)== 0 or len(password) == 0:
            return render_template("login.html",err="Masukkan data login!")
        else:
            cursor = mydb.cursor()
            cursor.execute("SELECT * FROM auth WHERE username='{}'".format(username))
            myresult = cursor.fetchone()
            if myresult == None:
                return render_template("login.html",err="Tidak ditemukan user tersebut!")
            else:
                if myresult[0]==username and myresult[1]==password:
                    session["admin"]=True
                    return redirect(url_for("dashboard"))
                else:
                    return render_template("login.html",err="Password yang dimasukkan salah!")
        return "anata no namaewo"
    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html")
    
@app.route("/prosestext")
def prosestext():
    if 'admin' not in session:
        return redirect(url_for("index"))
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM dataset")
    myresult = cursor.fetchall()

    factory = StopWordRemoverFactory()
    stopword = factory.create_stop_word_remover()

    payload = []

    for x in myresult:
        #### MELAKUKAN PROSES STEMMING STOPWORD BAHASA INDONESIA
        satu = stopword.remove(x[0])
        #### MENGHILANGKAN TEXT TIDAK PENTING SEPERTI HASHTAG DAN MENTION
        dua = re.sub(r"@[^\s]+"," ",satu)
        dua = re.sub(r"#[^\s]+"," ",dua)
        dua = re.sub(r"\."," ",dua)
        dua = re.sub(r"http[^\s]+"," ",dua)
        dua = re.sub(r"\?"," ",dua)
        dua = re.sub(r","," ",dua)
        dua = re.sub(r"”"," ",dua)
        dua = re.sub(r"co/[^\s]+"," ",dua)
        dua = re.sub(r":'\)"," ",dua)
        dua = re.sub(r":\)","",dua)
        dua = re.sub(r"&"," ",dua)
        dua = re.sub(r'\"([^\"]+)\"',"\g<1>",dua)
        dua = re.sub(r'\([^\)]+\"',"",dua)
        dua = re.sub(r'\((.+)\)',"\g<1>",dua)
        dua = re.sub(r'-'," ",dua)
        dua = re.sub(r':\('," ",dua)
        dua = re.sub(r':'," ",dua)
        dua = re.sub(r'\('," ",dua)
        dua = re.sub(r'\)'," ",dua)
        dua = re.sub(r"'"," ",dua)
        dua = re.sub(r'"'," ",dua)
        dua = re.sub(r';'," ",dua)
        dua = re.sub(r':v'," ",dua)
        dua = re.sub(r'²'," ",dua)
        dua = re.sub(r':"\)'," ",dua)
        dua = re.sub(r'\[\]'," ",dua)
        dua = re.sub(r'“',"",dua)
        dua = re.sub(r'_'," ",dua)
        dua = re.sub(r'—'," ",dua)
        dua = re.sub(r'…'," ",dua)
        dua = re.sub(r'='," ",dua)
        dua = re.sub(r'\/'," ",dua)
        dua = re.sub(r'\[\w+\]'," ",dua)
        dua = re.sub(r'!'," ",dua)
        dua = re.sub(r"'"," ",dua)
        dua = re.sub(r'\s+'," ",dua)
        dua = re.sub(r'^RT',"",dua) 
        dua = re.sub(r'\s+$',"",dua)   
        dua = re.sub(r'^\s+',"",dua)   
        #### CASE FOLDING
        tiga = dua.lower()
        #### MENGUBAH KATA SESUAI PANDUAN UMUM EJAAN BAHASA INDONESIA
        payload.append((tiga,x[1]))

    cursor = mydb.cursor()
    cursor.execute("DELETE FROM textprocessing")
    mydb.commit()

    sql = "INSERT INTO textprocessing (text,sentimen) VALUES (%s,%s)"
    cursor.executemany(sql,payload)
    mydb.commit()

    return redirect(url_for("textprocessing"))

@app.route('/textprocessing')
def textprocessing():
    if 'admin' not in session:
        return redirect(url_for("index"))
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM textprocessing")
    myresult = cursor.fetchall()
    cursor.execute("SELECT * FROM dataset")
    myresult2 = cursor.fetchall()

    arr = []
    count=0
    for x in myresult:
        count=count+1
        arr.append({"no":count,"sebelum":myresult2[count-1][0],"text":x[0],"sentimen":x[1]})
    
    return render_template("textprocessing.html",data=arr)

@app.route('/dataset')
def dataset():
    if 'admin' not in session:
        return redirect(url_for("index"))
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM dataset")
    myresult = cursor.fetchall()

    arr = []
    count=0
    for x in myresult:
        count=count+1
        arr.append({"no":count,"text":x[0],"sentimen":x[1]})
    
    return render_template('dataset.html',data=arr)


@app.route('/pengujian')
def pengujian():
    if 'admin' not in session:
        return redirect(url_for("index"))
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM textprocessing")
    myresult = cursor.fetchall()

    X = []
    y = []

    for l in myresult:
        X.append(l[0])
        y.append(l[1])

    X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.3, train_size=0.7, random_state=45)
    vectorizer = TfidfVectorizer(min_df=0.0, max_df=1.0, sublinear_tf=True, use_idf=True, stop_words='english')

    X_train_tf = vectorizer.fit_transform(X_train)
    X_test_tf = vectorizer.transform(X_test)

    model = MLPClassifier(hidden_layer_sizes=(30,15,19,39,),activation="relu",solver='adam')
    model.fit(X_train_tf, y_train)
    result = model.predict(X_test_tf)

    c=-1
    p = []
    for x in result:
        c=c+1
        p.append({"no":c+1,"text":X_test[c],"sentimen":x})
    
    matrix = confusion_matrix(y_test,result,labels=["Positive","Negative"])

    cmatrix = [{ "kosong": "Actual True", "actualtrue": int(matrix[0][0]), "actualfalse": int(matrix[0][1]) },{ "kosong": "Actual False", "actualtrue": int(matrix[1][0]), "actualfalse": int(matrix[1][1]) }]
    cmatrix_dump = json.dumps(cmatrix)
    return render_template("pengujian.html", cmatrix=cmatrix_dump)

@app.route('/klasifikasi')
def klasifikasi():
    if 'admin' not in session:
        return redirect(url_for("index"))
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM textprocessing")
    myresult = cursor.fetchall()

    X = []
    y = []

    for l in myresult:
        X.append(l[0])
        y.append(l[1])

    X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.3, train_size=0.7, random_state=45)
    vectorizer = TfidfVectorizer(min_df=0.0, max_df=1.0, sublinear_tf=True, use_idf=True, stop_words='english')

    X_train_tf = vectorizer.fit_transform(X_train)
    X_test_tf = vectorizer.transform(X_test)

    model = MLPClassifier(hidden_layer_sizes=(30,15,19,39),activation="relu",solver='adam')
    model.fit(X_train_tf, y_train)
    result = model.predict(X_test_tf)

    c=-1
    p = []
    for x in result:
        c=c+1
        p.append({"no":c+1,"text":X_test[c],"sentimen":x})
    print(p)
    #print(confusion_matrix(y_test,result,labels=["Positive","Negative"]))

    return render_template("klasifikasi.html", data=p)

@app.route('/importdataset', methods=['GET','POST'])
def importdataset():
    if 'admin' not in session:
        return redirect(url_for("index"))
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(url_for('dataset'))
        file = request.files['file']
        excel = pd.read_excel(file)

        cursor = mydb.cursor()
        cursor.execute("DELETE FROM dataset")
        mydb.commit()

        sql = "INSERT INTO dataset (text,sentimen) VALUES (%s,%s)"

        tupp = []
        counter=-1
        for x in excel["text"]:
            counter=counter+1
            tupp.append((x,excel["sentimen"][counter]))

        
        cursor.executemany(sql,tupp)
        mydb.commit()

        return redirect(url_for("dataset"))
        

@app.route('/debug')
def debug():
    if 'admin' not in session:
        return redirect(url_for("index"))
    csv = pd.read_excel("dataset.xlsx")

    factory = StopWordRemoverFactory()
    stopword = factory.create_stop_word_remover()

    print(stopword.remove("Kepala otak kau lek, medan aman atau berkah?"))
    return "sarjana kombur"

if __name__=='__main__':
    app.run(debug=True)
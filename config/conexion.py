import mysql.connector
conexion = mysql.connector.connect(
    host="b4ggqdsnh1uys4bcrqih-mysql.services.clever-cloud.com",
    user="ujzqm2pshctfolmk",
    password="APPNh8U3t8V3t1Abt1ie",
    database="b4ggqdsnh1uys4bcrqih"
)
if conexion.is_connected():
   print("conexion exitosa")